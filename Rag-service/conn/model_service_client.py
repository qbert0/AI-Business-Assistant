from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from utils.constants import (
    MODEL_SERVICE_EMBEDDING_MODEL_ID,
    MODEL_SERVICE_EMBEDDING_USE_CASE,
    MODEL_SERVICE_INFERENCE_USE_CASE,
    MODEL_SERVICE_LLM_MODEL_ID,
    MODEL_SERVICE_MAX_RETRIES,
    MODEL_SERVICE_ORGANIZATION_ID,
    MODEL_SERVICE_RETRY_BACKOFF_SECONDS,
    MODEL_SERVICE_TIMEOUT_SECONDS,
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
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or MODEL_SERVICE_URL).rstrip("/")
        self.organization_id = organization_id or MODEL_SERVICE_ORGANIZATION_ID
        self.llm_model_id = llm_model_id or MODEL_SERVICE_LLM_MODEL_ID
        self.embedding_model_id = embedding_model_id or MODEL_SERVICE_EMBEDDING_MODEL_ID
        self.inference_use_case = inference_use_case or MODEL_SERVICE_INFERENCE_USE_CASE
        self.embedding_use_case = embedding_use_case or MODEL_SERVICE_EMBEDDING_USE_CASE
        self.timeout_seconds = timeout_seconds or MODEL_SERVICE_TIMEOUT_SECONDS
        self.max_retries = MODEL_SERVICE_MAX_RETRIES if max_retries is None else max(0, max_retries)
        self.retry_backoff_seconds = (
            MODEL_SERVICE_RETRY_BACKOFF_SECONDS
            if retry_backoff_seconds is None
            else max(0.0, retry_backoff_seconds)
        )

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
        last_exc: Exception | None = None
        attempts = self.max_retries + 1

        for attempt in range(1, attempts + 1):
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
                last_exc = exc
                if attempt >= attempts or not self._is_retryable_error(exc):
                    logger.error(f"Model service request failed for path={path}: {exc}")
                    raise ValueError(f"Model service request failed for path={path}: {exc}") from exc

                delay = self.retry_backoff_seconds * attempt
                logger.warning(
                    "Transient model service request failed "
                    f"path={path} attempt={attempt}/{attempts} retry_in={delay:.1f}s error={exc}"
                )
                await asyncio.sleep(delay)

        raise ValueError(f"Model service request failed for path={path}: {last_exc}")

    @staticmethod
    def _is_retryable_error(exc: Exception) -> bool:
        if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)):
            return True

        if isinstance(exc, httpx.HTTPStatusError):
            return exc.response.status_code in {502, 503, 504}

        return False

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
