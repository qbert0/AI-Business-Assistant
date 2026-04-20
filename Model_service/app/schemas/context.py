from typing import Any, Literal

from pydantic import BaseModel, Field


MessageRole = Literal["system", "user", "assistant"]


class ConversationMessage(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1)


class ContextItem(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextBuildRequest(BaseModel):
    conversation_id: str | None = None
    organization_id: str | None = None
    user_id: str | None = None
    query: str = Field(..., min_length=1)
    history: list[ConversationMessage] = Field(default_factory=list)
    external_contexts: list[ContextItem] = Field(default_factory=list)
    system_prompt: str | None = None
    max_history_messages: int = Field(12, ge=1, le=100)


class ContextBuildResponse(BaseModel):
    system_prompt: str
    messages: list[ConversationMessage]
    context_items: list[ContextItem]
    token_estimate: int
