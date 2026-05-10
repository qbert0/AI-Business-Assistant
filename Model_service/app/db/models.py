from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


def uuid_pk():
    return Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()), server_default=text("UUID()"))


class Provider(Base):
    __tablename__ = "model_providers"

    id = uuid_pk()
    name = Column(String(120), nullable=False, unique=True, index=True)
    provider_type = Column(String(60), nullable=False, index=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}", server_default="{}")
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    models = relationship("RegisteredModel", back_populates="provider", cascade="all, delete-orphan")


class RegisteredModel(Base):
    __tablename__ = "registered_models"

    id = uuid_pk()
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    display_name = Column(String(160), nullable=False, index=True)
    model_name = Column(String(160), nullable=False, index=True)
    base_url = Column(String(500), nullable=False)
    api_key_encrypted = Column(Text, nullable=True)
    api_key_masked = Column(String(255), nullable=True)
    capabilities_json = Column(Text, nullable=False, default="[]", server_default="[]")
    parameters_json = Column(Text, nullable=False, default="{}", server_default="{}")
    priority = Column(Integer, nullable=False, default=100, server_default="100")
    is_default = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    health_status = Column(String(50), nullable=False, default="unknown", server_default="unknown")
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    provider = relationship("Provider", back_populates="models")
    default_policies = relationship(
        "ModelPolicy",
        back_populates="default_model",
        foreign_keys="ModelPolicy.default_model_id",
    )
    fallback_policies = relationship(
        "ModelPolicy",
        back_populates="fallback_model",
        foreign_keys="ModelPolicy.fallback_model_id",
    )
    inference_requests = relationship("InferenceRequest", back_populates="model")
    feedback_events = relationship("FeedbackEvent", back_populates="model")
    metric_rollups = relationship("MetricRollup", back_populates="model", cascade="all, delete-orphan")


class ModelPolicy(Base):
    __tablename__ = "model_policies"

    id = uuid_pk()
    organization_id = Column(String(64), nullable=True, index=True)
    use_case = Column(String(80), nullable=False, default="chat_advisory", server_default="chat_advisory", index=True)
    default_model_id = Column(String(36), ForeignKey("registered_models.id", ondelete="RESTRICT"), nullable=False)
    fallback_model_id = Column(String(36), ForeignKey("registered_models.id", ondelete="SET NULL"), nullable=True)
    temperature = Column(Float, nullable=False, default=0.2, server_default="0.2")
    max_tokens = Column(Integer, nullable=False, default=40000, server_default="40000")
    system_prompt = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}", server_default="{}")
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    default_model = relationship("RegisteredModel", foreign_keys=[default_model_id], back_populates="default_policies")
    fallback_model = relationship("RegisteredModel", foreign_keys=[fallback_model_id], back_populates="fallback_policies")
    inference_requests = relationship("InferenceRequest", back_populates="policy")


class InferenceRequest(Base):
    __tablename__ = "inference_requests"

    id = uuid_pk()
    conversation_id = Column(String(64), nullable=True, index=True)
    organization_id = Column(String(64), nullable=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    model_id = Column(String(36), ForeignKey("registered_models.id", ondelete="RESTRICT"), nullable=False, index=True)
    policy_id = Column(String(36), ForeignKey("model_policies.id", ondelete="SET NULL"), nullable=True, index=True)
    question = Column(Text, nullable=False)
    request_payload_json = Column(Text, nullable=False, default="{}", server_default="{}")
    assembled_context_json = Column(Text, nullable=False, default="{}", server_default="{}")
    status = Column(String(30), nullable=False, default="pending", server_default="pending", index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    model = relationship("RegisteredModel", back_populates="inference_requests")
    policy = relationship("ModelPolicy", back_populates="inference_requests")
    response = relationship("InferenceResponse", back_populates="request", uselist=False, cascade="all, delete-orphan")
    context_snapshots = relationship("ContextSnapshot", back_populates="request", cascade="all, delete-orphan")
    feedback_events = relationship("FeedbackEvent", back_populates="request")


class InferenceResponse(Base):
    __tablename__ = "inference_responses"

    id = uuid_pk()
    request_id = Column(String(36), ForeignKey("inference_requests.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    response_text = Column(Text, nullable=False)
    finish_reason = Column(String(40), nullable=True)
    raw_response_json = Column(Text, nullable=False, default="{}", server_default="{}")
    prompt_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    completion_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    total_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    estimated_cost = Column(Float, nullable=False, default=0.0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("InferenceRequest", back_populates="response")


class ContextSnapshot(Base):
    __tablename__ = "context_snapshots"

    id = uuid_pk()
    conversation_id = Column(String(64), nullable=True, index=True)
    organization_id = Column(String(64), nullable=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    request_id = Column(String(36), ForeignKey("inference_requests.id", ondelete="CASCADE"), nullable=True, index=True)
    query_text = Column(Text, nullable=False)
    items_json = Column(Text, nullable=False, default="[]", server_default="[]")
    token_estimate = Column(Integer, nullable=False, default=0, server_default="0")
    source = Column(String(60), nullable=False, default="assembled", server_default="assembled")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("InferenceRequest", back_populates="context_snapshots")


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id = uuid_pk()
    request_id = Column(String(36), ForeignKey("inference_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(String(64), nullable=True, index=True)
    organization_id = Column(String(64), nullable=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    model_id = Column(String(36), ForeignKey("registered_models.id", ondelete="SET NULL"), nullable=True, index=True)
    rating = Column(String(20), nullable=False, index=True)
    comment = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}", server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("InferenceRequest", back_populates="feedback_events")
    model = relationship("RegisteredModel", back_populates="feedback_events")


class MetricRollup(Base):
    __tablename__ = "metric_rollups"
    __table_args__ = (
        UniqueConstraint("model_id", "bucket_start", "bucket_granularity", name="unique_model_metric_bucket"),
    )

    id = uuid_pk()
    model_id = Column(String(36), ForeignKey("registered_models.id", ondelete="CASCADE"), nullable=False, index=True)
    bucket_start = Column(DateTime(timezone=True), nullable=False, index=True)
    bucket_granularity = Column(String(20), nullable=False, default="hour", server_default="hour")
    request_count = Column(Integer, nullable=False, default=0, server_default="0")
    success_count = Column(Integer, nullable=False, default=0, server_default="0")
    error_count = Column(Integer, nullable=False, default=0, server_default="0")
    avg_latency_ms = Column(Float, nullable=False, default=0.0, server_default="0")
    total_latency_ms = Column(Integer, nullable=False, default=0, server_default="0")
    prompt_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    completion_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    total_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    estimated_cost = Column(Float, nullable=False, default=0.0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    model = relationship("RegisteredModel", back_populates="metric_rollups")
