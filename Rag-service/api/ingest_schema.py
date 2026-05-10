from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChunkPayload(BaseModel):
    chunk_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestChunksRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    document_name: str = Field(..., min_length=1)
    source: str = Field("worker-service", min_length=1)
    source_description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunks: list[ChunkPayload] = Field(..., min_length=1)
