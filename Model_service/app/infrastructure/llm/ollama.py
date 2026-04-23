from typing import Any

import httpx

from app.infrastructure.llm.base import BaseLLMClient, HealthCheckResult, LLMResult, ProviderRequestError


class OllamaClient(BaseLLMClient):
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
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if metadata:
            payload["metadata"] = metadata

        endpoint = f"{self.base_url}/api/chat"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        message = data.get("message") or {}
        prompt_tokens = int(data.get("prompt_eval_count") or 0)
        completion_tokens = int(data.get("eval_count") or 0)
        total_tokens = prompt_tokens + completion_tokens
        return LLMResult(
            response_text=message.get("content") or "",
            finish_reason=data.get("done_reason"),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            raw_response=data,
        )

    def health_check(self) -> HealthCheckResult:
        endpoint = f"{self.base_url}/api/tags"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(endpoint)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"Ollama health check failed: {exc}") from exc
        return HealthCheckResult(status="healthy", detail="Connected to upstream Ollama endpoint.")
