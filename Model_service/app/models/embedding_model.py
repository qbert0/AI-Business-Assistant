from typing import Any

from pydantic import BaseModel, Field


class EmbeddingCreate(BaseModel):
    model_id: str | None = None
    model: str | None = None
    organization_id: str | None = None
    use_case: str = Field("embeddings", min_length=1, max_length=80)
    input: list[str] = Field(..., min_items=1)
    dimensions: int | None = Field(None, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbeddingVectorRead(BaseModel):
    index: int
    embedding: list[float]


class EmbeddingUsageRead(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingResultRead(BaseModel):
    model_id: str
    model_name: str
    provider_type: str
    dimensions: int
    data: list[EmbeddingVectorRead]
    usage: EmbeddingUsageRead
