from __future__ import annotations

from typing import Any

import httpx

from utils.constants import SERVER_SERVICE_URL
from utils.logs import logger


class ServerServiceClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: float = 120.0) -> None:
        self.base_url = (base_url or SERVER_SERVICE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def download_file(self, content_url: str) -> bytes:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(content_url)
                response.raise_for_status()
                return response.content
        except Exception as exc:
            logger.error(f"Server file download failed url={content_url}: {exc}")
            raise ValueError(f"Server file download failed: {exc}") from exc

    async def get_pipeline(self, document_id: str, acting_user_id: str) -> dict[str, Any]:
        return await self._request_json(
            "GET",
            f"/documents/{document_id}/pipeline",
            query={"acting_user_id": acting_user_id},
        )

    async def update_document_status(
        self,
        document_id: str,
        acting_user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._request_json(
            "PATCH",
            f"/documents/{document_id}/status",
            query={"acting_user_id": acting_user_id},
            payload=payload,
        )

    async def is_cancel_requested(self, document_id: str, acting_user_id: str) -> bool:
        pipeline = await self.get_pipeline(document_id, acting_user_id)
        metadata = pipeline.get("document", {}).get("metadata") or {}
        analysis = metadata.get("analysis") if isinstance(metadata, dict) else {}
        return bool(isinstance(analysis, dict) and analysis.get("cancel_requested"))

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    params=query,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.error(f"Server service request failed method={method} path={path}: {exc}")
            raise ValueError(f"Server service request failed method={method} path={path}: {exc}") from exc
