from __future__ import annotations

from typing import Any

import httpx

from utils.constants import RAG_SERVICE_URL
from utils.logs import logger


class RagServiceClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = (base_url or RAG_SERVICE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def ingest_chunks(
        self,
        *,
        document_id: str,
        document_name: str,
        source: str,
        chunks: list[dict[str, Any]],
        source_description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "document_id": document_id,
            "document_name": document_name,
            "source": source,
            "source_description": source_description,
            "metadata": metadata or {},
            "chunks": chunks,
        }
        return await self._post_json("/ingest/chunks", payload)

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{self.base_url}{path}", json=payload)
                if response.is_error:
                    raise httpx.HTTPStatusError(
                        f"{response.status_code} response from rag service: {response.text}",
                        request=response.request,
                        response=response,
                    )
                return response.json()
        except httpx.TimeoutException as exc:
            logger.error(
                "Rag service request timed out "
                f"path={path} base_url={self.base_url} timeout_seconds={self.timeout_seconds} "
                f"payload_keys={list(payload.keys())}"
            )
            raise ValueError(
                f"Rag service request timed out for path={path} after {self.timeout_seconds}s"
            ) from exc
        except httpx.HTTPStatusError as exc:
            response_text = ""
            response = getattr(exc, "response", None)
            if response is not None:
                with_response = getattr(response, "text", "")
                response_text = with_response[:4000] if with_response else ""
            logger.error(
                "Rag service returned HTTP error "
                f"path={path} base_url={self.base_url} "
                f"status_code={response.status_code if response is not None else 'unknown'} "
                f"response_text={response_text}"
            )
            raise ValueError(
                f"Rag service returned HTTP error for path={path}: "
                f"{response.status_code if response is not None else 'unknown'} {response_text}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error(
                "Rag service connection error "
                f"path={path} base_url={self.base_url} error_type={type(exc).__name__} error={exc}"
            )
            raise ValueError(
                f"Rag service connection error for path={path}: {type(exc).__name__}: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(
                "Unexpected rag service request failure "
                f"path={path} base_url={self.base_url} error_type={type(exc).__name__} error={exc}"
            )
            raise ValueError(
                f"Unexpected rag service request failure for path={path}: {type(exc).__name__}: {exc}"
            ) from exc
