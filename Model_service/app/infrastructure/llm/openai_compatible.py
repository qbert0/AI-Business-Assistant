from typing import Any

import httpx

from app.infrastructure.llm.base import BaseLLMClient, HealthCheckResult, LLMResult, ProviderRequestError


class OpenAICompatibleClient(BaseLLMClient):
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
            "stream": False,
        }
        if metadata:
            payload["metadata"] = metadata

        endpoint = f"{self.base_url}/chat/completions"
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

    def health_check(self) -> HealthCheckResult:
        endpoint = f"{self.base_url}/models"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(endpoint, headers=self._headers())
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"OpenAI-compatible health check failed: {exc}") from exc
        return HealthCheckResult(status="healthy", detail="Connected to upstream OpenAI-compatible endpoint.")
