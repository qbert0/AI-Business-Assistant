from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


def uuid_pk():
    return Column(String(36), primary_key=True, index=True, default=lambda: str(uuid4()), server_default=text("UUID()"))


class User(Base):
    __tablename__ = "users"

    id = uuid_pk()
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)
    public_profile = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    default_organization_id = Column(String(36), nullable=True)
    locale = Column(String(20), nullable=False, default="vi", server_default="vi")
    timezone = Column(String(80), nullable=False, default="Asia/Saigon", server_default="Asia/Saigon")
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("1"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Organization(Base):
    __tablename__ = "organizations"

    id = uuid_pk()
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    sensitive_restrictions = Column(Text, nullable=True)
    billing_plan = Column(String(100), nullable=False, default="free", server_default="free")
    billing_status = Column(String(50), nullable=False, default="trialing", server_default="trialing")
    settings_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="organization", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="organization", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="organization")
    billing_records = relationship("BillingRecord", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("user_id", "organization_id", name="unique_user_org"),)

    id = uuid_pk()
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(30), nullable=False, default="user", server_default="user")
    permissions = Column(Text, nullable=False, default="[]")
    status = Column(String(30), nullable=False, default="active", server_default="active")
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="members")


class Document(Base):
    __tablename__ = "documents"

    id = uuid_pk()
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=False)
    status = Column(String(40), nullable=False, default="processing", server_default="processing")
    chunk_count = Column(String(20), nullable=False, default="0", server_default="0")
    embedding_model = Column(String(120), nullable=False, default="text-embedding-3-small", server_default="text-embedding-3-small")
    vector_index = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="documents")
    uploader = relationship("User")
    pipeline_events = relationship("PipelineEvent", back_populates="document", cascade="all, delete-orphan")


class PipelineEvent(Base):
    __tablename__ = "pipeline_events"

    id = uuid_pk()
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    stage = Column(String(80), nullable=False)
    status = Column(String(40), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="pipeline_events")
    actor = relationship("User")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = uuid_pk()
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    context_type = Column(String(30), nullable=False, default="organization", server_default="organization")
    title = Column(String(255), nullable=False)
    is_pinned = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="chat_sessions")
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = uuid_pk()
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")
    feedback = relationship("ChatFeedback", back_populates="message", cascade="all, delete-orphan")


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = uuid_pk()
    message_id = Column(String(36), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(String(20), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    message = relationship("ChatMessage", back_populates="feedback")
    user = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = uuid_pk()
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    notification_type = Column(String(50), nullable=False, default="system", server_default="system")
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    action_url = Column(String(500), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
    organization = relationship("Organization", back_populates="notifications")


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id = uuid_pk()
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    plan = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending", server_default="pending")
    amount = Column(String(40), nullable=False, default="0", server_default="0")
    currency = Column(String(10), nullable=False, default="VND", server_default="VND")
    provider = Column(String(80), nullable=False, default="manual", server_default="manual")
    provider_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship("Organization", back_populates="billing_records")
    created_by = relationship("User")
