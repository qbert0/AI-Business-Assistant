import json
from typing import Any

import httpx

from app.infrastructure.llm.base import BaseLLMClient, HealthCheckResult, LLMResult, ProviderRequestError


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(
        self,
        base_url: str,
        model_name: str,
        api_key: str | None,
        timeout_seconds: int,
        stream_response: bool = True,
    ) -> None:
        super().__init__(base_url, model_name, api_key, timeout_seconds)
        self.stream_response = stream_response

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResult:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": self.stream_response,
        }
        if metadata:
            payload["metadata"] = metadata

        endpoint = f"{self.base_url}/chat/completions"
        if self.stream_response:
            return self._chat_stream(endpoint, payload)

        return self._chat_json(endpoint, payload)

    def _chat_json(self, endpoint: str, payload: dict[str, Any]) -> LLMResult:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(endpoint, headers=self._headers(), json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"OpenAI-compatible request failed: {exc}") from exc

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise ProviderRequestError("OpenAI-compatible response did not include any choices.")
        message = choices[0].get("message") or {}
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        return LLMResult(
            response_text=message.get("content") or "",
            finish_reason=choices[0].get("finish_reason"),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            raw_response=data,
        )

    def _chat_stream(self, endpoint: str, payload: dict[str, Any]) -> LLMResult:
        content_parts: list[str] = []
        finish_reason: str | None = None
        usage: dict[str, Any] = {}
        chunk_count = 0

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                with client.stream("POST", endpoint, headers=self._headers(), json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue

                        data_line = line.strip()
                        if data_line.startswith("data:"):
                            data_line = data_line[len("data:") :].strip()
                        if data_line == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_line)
                        except json.JSONDecodeError:
                            continue

                        chunk_count += 1
                        if isinstance(chunk.get("usage"), dict):
                            usage = chunk["usage"]

                        choices = chunk.get("choices") or []
                        if not choices:
                            continue

                        choice = choices[0] or {}
                        finish_reason = choice.get("finish_reason") or finish_reason
                        delta = choice.get("delta") or {}
                        message = choice.get("message") or {}
                        text = delta.get("content") or message.get("content")
                        if text:
                            content_parts.append(text)
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"OpenAI-compatible streaming request failed: {exc}") from exc

        response_text = "".join(content_parts)
        if not response_text:
            raise ProviderRequestError("OpenAI-compatible streaming response did not include any content.")

        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        return LLMResult(
            response_text=response_text,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            raw_response={
                "stream": True,
                "chunk_count": chunk_count,
                "usage": usage,
                "finish_reason": finish_reason,
            },
        )

    def health_check(self) -> HealthCheckResult:
        endpoint = f"{self.base_url}/models"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(endpoint, headers=self._headers())
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"OpenAI-compatible health check failed: {exc}") from exc
        return HealthCheckResult(status="healthy", detail="Connected to upstream OpenAI-compatible endpoint.")
