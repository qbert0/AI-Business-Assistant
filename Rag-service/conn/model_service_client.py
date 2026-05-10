from __future__ import annotations

from typing import Any, Optional

import httpx

from utils.constants import (
    MODEL_SERVICE_EMBEDDING_MODEL_ID,
    MODEL_SERVICE_EMBEDDING_USE_CASE,
    MODEL_SERVICE_INFERENCE_USE_CASE,
    MODEL_SERVICE_LLM_MODEL_ID,
    MODEL_SERVICE_ORGANIZATION_ID,
    MODEL_SERVICE_URL,
)
from utils.logs import logger


class ModelServiceClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        organization_id: Optional[str] = None,
        llm_model_id: Optional[str] = None,
        embedding_model_id: Optional[str] = None,
        inference_use_case: Optional[str] = None,
        embedding_use_case: Optional[str] = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = (base_url or MODEL_SERVICE_URL).rstrip("/")
        self.organization_id = organization_id or MODEL_SERVICE_ORGANIZATION_ID
        self.llm_model_id = llm_model_id or MODEL_SERVICE_LLM_MODEL_ID
        self.embedding_model_id = embedding_model_id or MODEL_SERVICE_EMBEDDING_MODEL_ID
        self.inference_use_case = inference_use_case or MODEL_SERVICE_INFERENCE_USE_CASE
        self.embedding_use_case = embedding_use_case or MODEL_SERVICE_EMBEDDING_USE_CASE
        self.timeout_seconds = timeout_seconds

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
            return True
        except Exception as exc:
            logger.error(f"Model service health check failed: {exc}")
            return False

    async def create_inference(
        self,
        question: str,
        *,
        system_prompt: str | None = None,
        history: Optional[list[dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        payload = {
            "organization_id": self.organization_id,
            "model_id": self.llm_model_id,
            "use_case": self.inference_use_case,
            "question": question,
            "history": history or [],
            "external_contexts": [],
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "metadata": metadata or {},
        }
        return await self._post_json("/api/v1/inferences", payload)

    async def create_embeddings(
        self,
        input_texts: list[str],
        *,
        dimensions: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        payload = {
            "organization_id": self.organization_id,
            "model_id": self.embedding_model_id,
            "use_case": self.embedding_use_case,
            "input": input_texts,
            "dimensions": dimensions,
            "metadata": metadata or {},
        }
        return await self._post_json("/api/v1/embeddings", payload)

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}{path}",
                    json=self._normalize_json_value(payload),
                )
                if response.is_error:
                    raise httpx.HTTPStatusError(
                        f"{response.status_code} response from model service: {response.text}",
                        request=response.request,
                        response=response,
                    )
                return response.json()
        except Exception as exc:
            logger.error(f"Model service request failed for path={path}: {exc}")
            raise ValueError(f"Model service request failed for path={path}: {exc}") from exc

    @classmethod
    def _normalize_json_value(cls, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {str(key): cls._normalize_json_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [cls._normalize_json_value(item) for item in value]
        if hasattr(value, "value"):
            return cls._normalize_json_value(getattr(value, "value"))
        if hasattr(value, "model_dump"):
            return cls._normalize_json_value(value.model_dump())
        return str(value)
