from __future__ import annotations

from pydantic import BaseModel, Field


class SearchNodesRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=50)
    group_id: str | None = None


class SearchFactsRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=50)
    center_node_uuid: str | None = None
    group_id: str | None = None
