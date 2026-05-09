from typing import Any

import httpx

from app.infrastructure.embedding.base import BaseEmbeddingClient, EmbeddingResult, EmbeddingVector, ProviderRequestError


class OpenAICompatibleEmbeddingClient(BaseEmbeddingClient):
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def embed(
        self,
        inputs: list[str],
        *,
        dimensions: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EmbeddingResult:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "input": inputs,
            "encoding_format": "float",
        }
        if dimensions is not None:
            payload["dimensions"] = dimensions
        if metadata:
            payload["metadata"] = metadata

        endpoint = f"{self.base_url}/embeddings"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(endpoint, headers=self._headers(), json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"OpenAI-compatible embedding request failed: {exc}") from exc

        data = response.json()
        items = data.get("data") or []
        if not items:
            raise ProviderRequestError("OpenAI-compatible embedding response did not include any vectors.")
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or prompt_tokens)
        return EmbeddingResult(
            vectors=[
                EmbeddingVector(
                    index=int(item.get("index") or 0),
                    embedding=[float(value) for value in (item.get("embedding") or [])],
                )
                for item in items
            ],
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
            raw_response=data,
        )
