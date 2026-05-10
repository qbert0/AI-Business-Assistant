from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.context_model import ContextBuildResponse, ContextItem, ConversationMessage


class InferenceCreate(BaseModel):
    conversation_id: str | None = None
    organization_id: str | None = None
    user_id: str | None = None
    model_id: str | None = None
    model: str | None = None
    use_case: str = Field("chat_advisory", min_length=1, max_length=80)
    question: str = Field(..., min_length=1)
    history: list[ConversationMessage] = Field(default_factory=list)
    external_contexts: list[ContextItem] = Field(default_factory=list)
    system_prompt: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=40000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InferenceRequestRead(BaseModel):
    id: str
    conversation_id: str | None
    organization_id: str | None
    user_id: str | None
    model_id: str
    policy_id: str | None
    question: str
    status: str
    latency_ms: int | None
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class InferenceResponseRead(BaseModel):
    id: str
    request_id: str
    response_text: str
    finish_reason: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    created_at: datetime


class InferenceResult(BaseModel):
    request: InferenceRequestRead
    response: InferenceResponseRead
    context: ContextBuildResponse


class InferenceListItem(BaseModel):
    request: InferenceRequestRead
    response: InferenceResponseRead | None
