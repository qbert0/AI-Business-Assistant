from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    request_id: str | None = None
    conversation_id: str | None = None
    organization_id: str | None = None
    user_id: str = Field(..., min_length=1, max_length=64)
    model_id: str | None = None
    rating: Literal["positive", "negative"]
    comment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackRead(BaseModel):
    id: str
    request_id: str | None
    conversation_id: str | None
    organization_id: str | None
    user_id: str
    model_id: str | None
    rating: str
    comment: str | None
    metadata: dict[str, Any]
    created_at: datetime
