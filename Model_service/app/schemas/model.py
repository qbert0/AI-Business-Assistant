from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    provider_id: str
    display_name: str = Field(..., min_length=2, max_length=160)
    model_name: str = Field(..., min_length=1, max_length=160)
    base_url: str = Field(..., min_length=3, max_length=500)
    api_key: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(100, ge=0, le=1000)
    is_default: bool = False
    is_active: bool = True


class ModelUpdate(BaseModel):
    provider_id: str | None = None
    display_name: str | None = Field(None, min_length=2, max_length=160)
    model_name: str | None = Field(None, min_length=1, max_length=160)
    base_url: str | None = Field(None, min_length=3, max_length=500)
    api_key: str | None = None
    capabilities: list[str] | None = None
    parameters: dict[str, Any] | None = None
    priority: int | None = Field(None, ge=0, le=1000)
    is_default: bool | None = None
    is_active: bool | None = None


class ModelRead(BaseModel):
    id: str
    provider_id: str
    display_name: str
    model_name: str
    base_url: str
    api_key_masked: str | None
    capabilities: list[str]
    parameters: dict[str, Any]
    priority: int
    is_default: bool
    is_active: bool
    health_status: str
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ModelHealthCheckRead(BaseModel):
    model_id: str
    status: str
    detail: str
    checked_at: datetime


class PolicyCreate(BaseModel):
    organization_id: str | None = None
    use_case: str = Field("chat_advisory", min_length=1, max_length=80)
    default_model_id: str
    fallback_model_id: str | None = None
    temperature: float = Field(0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(1200, ge=1, le=8192)
    system_prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PolicyUpdate(BaseModel):
    organization_id: str | None = None
    use_case: str | None = Field(None, min_length=1, max_length=80)
    default_model_id: str | None = None
    fallback_model_id: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=8192)
    system_prompt: str | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class PolicyRead(BaseModel):
    id: str
    organization_id: str | None
    use_case: str
    default_model_id: str
    fallback_model_id: str | None
    temperature: float
    max_tokens: int
    system_prompt: str | None
    metadata: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
