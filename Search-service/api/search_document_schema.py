from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from search_engines.base import SearchDeleteResult, SearchDocument


class SearchDocumentCreateRequest(BaseModel):
    index_name: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    document: dict[str, Any] = Field(default_factory=dict)
    refresh: bool = True


class SearchDocumentUpdateRequest(BaseModel):
    document: dict[str, Any] = Field(default_factory=dict)
    refresh: bool = True


class SearchDocumentRead(BaseModel):
    backend: str
    index_name: str
    document_id: str
    document: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None
    version: int | None = None

    @classmethod
    def from_domain(cls, *, backend: str, document: SearchDocument) -> "SearchDocumentRead":
        return cls(
            backend=backend,
            index_name=document.index_name,
            document_id=document.document_id,
            document=document.document,
            result=document.result,
            version=document.version,
        )


class SearchDocumentDeleteRead(BaseModel):
    backend: str
    index_name: str
    document_id: str
    deleted: bool
    result: str | None = None

    @classmethod
    def from_domain(
        cls,
        *,
        backend: str,
        result: SearchDeleteResult,
    ) -> "SearchDocumentDeleteRead":
        return cls(
            backend=backend,
            index_name=result.index_name,
            document_id=result.document_id,
            deleted=result.deleted,
            result=result.result,
        )
