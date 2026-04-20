from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ProviderType = Literal["openai_compatible", "ollama"]


class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    provider_type: ProviderType
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ProviderUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    provider_type: ProviderType | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class ProviderRead(BaseModel):
    id: str
    name: str
    provider_type: str
    description: str | None
    metadata: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
