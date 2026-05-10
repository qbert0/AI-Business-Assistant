from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

DocumentStatus = Literal["uploaded", "processing", "processed", "indexing", "indexed", "completed", "failed"]


Permission = Literal[
    "access_org_settings",
    "chat_advisory",
    "read_documents",
    "view_employees",
    "upload_documents",
    "view_analytics",
    "edit_sensitive_restrictions",
    "delete_chat_sessions",
]


class ApiInfo(BaseModel):
    name: str
    version: str
    docs_url: str
    health_url: str
    capabilities: list[str]


class UserCreate(BaseModel):
    email: EmailStr = Field(..., examples=["linh@acme.vn"])
    full_name: str = Field(..., min_length=2, max_length=255, examples=["Nguyen Linh"])
    password: str | None = Field(None, min_length=8, description="Bat buoc neu tao user de dang nhap bang email/password.")


class UserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    public_profile: str | None = None
    avatar_url: str | None = None
    default_organization_id: str | None = None
    locale: str
    timezone: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["Acme Vietnam"])
    industry: str | None = Field(None, examples=["Technology"])
    description: str | None = Field(None, examples=["Internal knowledge assistant for HR and operations."])
    owner_user_id: str = Field(..., description="User tao to chuc va tro thanh admin dau tien.")


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    industry: str | None = None
    description: str | None = None
    billing_plan: str | None = Field(None, examples=["free", "business", "enterprise"])


class OrganizationRead(BaseModel):
    id: str
    name: str
    industry: str | None
    description: str | None
    sensitive_restrictions: str | None
    billing_plan: str
    billing_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationDashboard(BaseModel):
    organization: OrganizationRead
    employee_count: int
    document_count: int
    indexed_document_count: int
    chat_session_count: int
    suggested_questions: list[str]


class MemberCreate(BaseModel):
    user_id: str = Field(..., description="User da ton tai trong he thong.")
    role: Literal["admin", "user"] = "user"
    permissions: list[Permission] | None = Field(None, description="Neu bo trong, server dung permission mac dinh theo role.")
    status: Literal["invited", "active"] = "active"


class MemberPatch(BaseModel):
    role: Literal["admin", "user"] | None = None
    permissions: list[Permission] | None = None
    status: Literal["invited", "active", "disabled"] | None = None


class MemberRead(BaseModel):
    id: str
    user_id: str
    organization_id: str
    role: str
    permissions: list[str]
    status: str
    joined_at: datetime
    user: UserRead

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    uploaded_by_user_id: str = Field(..., description="User upload tai lieu.")
    file_name: str = Field(..., examples=["employee-handbook.pdf"])
    source_url: str = Field(..., examples=["s3://bucket/employee-handbook.pdf"])
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentPresignedUploadRequest(BaseModel):
    acting_user_id: str = Field(..., description="User xin URL upload, can quyen upload_documents.")
    file_name: str = Field(..., min_length=1, examples=["employee-handbook.pdf"])
    content_type: str | None = Field(None, examples=["application/pdf"])
    expires: int = Field(3600, ge=60, le=86400, description="So giay hieu luc cua presigned URL.")


class DocumentPresignedUploadRead(BaseModel):
    bucket: str
    object_key: str
    upload_url: str
    source_url: str
    expires_in: int
    content_type: str | None = None


class DocumentPresignedUploadCompleteRequest(BaseModel):
    acting_user_id: str = Field(..., description="User hoan tat upload, can quyen upload_documents.")
    file_name: str = Field(..., min_length=1, examples=["employee-handbook.pdf"])
    bucket: str = Field(..., min_length=1)
    object_key: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1, examples=["s3://business-documents/organizations/org-1/file.pdf"])
    content_type: str | None = Field(None, examples=["application/pdf"])
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentPresignedDownloadRead(BaseModel):
    document_id: str
    file_name: str
    download_url: str
    expires_in: int


class DocumentStatusPatch(BaseModel):
    status: DocumentStatus | None = None
    chunk_count: int | None = Field(None, ge=0)
    embedding_model: str | None = None
    vector_index: str | None = None
    stage: str | None = Field(None, description="Pipeline stage vua cap nhat, vi du chunking/embedding/indexing.")
    message: str | None = None


class PipelineEventRead(BaseModel):
    id: str
    organization_id: str
    document_id: str
    actor_user_id: str | None
    stage: str
    status: str
    message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentRead(BaseModel):
    id: str
    organization_id: str
    uploaded_by_user_id: str | None
    file_name: str
    source_url: str
    status: str
    chunk_count: int
    embedding_model: str
    vector_index: str | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DocumentPipeline(BaseModel):
    document: DocumentRead
    events: list[PipelineEventRead]


class DocumentPreviewRead(BaseModel):
    document_id: str
    file_name: str
    kind: Literal["text", "image", "pdf", "download"]
    content: str | None = None
    message: str | None = None


class DocumentSearchRequest(BaseModel):
    user_id: str = Field(..., description="User thuc hien tim kiem, can quyen read_documents.")
    query: str = Field(..., min_length=1)
    size: int = Field(10, ge=1, le=50)


class DocumentSearchHit(BaseModel):
    document_id: str
    file_name: str
    source_url: str
    score: float | None = None
    document: dict[str, Any] = Field(default_factory=dict)


class ChatSessionCreate(BaseModel):
    user_id: str
    title: str = Field("New conversation", max_length=255)
    context_type: Literal["personal", "organization"] = "organization"


class ChatSessionRead(BaseModel):
    id: str
    organization_id: str | None
    user_id: str
    context_type: str
    title: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Citation(BaseModel):
    document_id: str
    file_name: str
    source_url: str


class ChatAsk(BaseModel):
    user_id: str
    question: str = Field(..., min_length=1, examples=["Chinh sach nghi phep cua cong ty nhu the nao?"])
    session_id: str | None = Field(None, description="Neu khong truyen, server tao session moi sau message dau tien.")


class ChatMessageRead(BaseModel):
    id: str
    session_id: str
    sender_type: str
    content: str
    citations: list[Citation]
    created_at: datetime


class ChatAnswer(BaseModel):
    session: ChatSessionRead
    user_message: ChatMessageRead
    assistant_message: ChatMessageRead
    answer: str
    citations: list[Citation]
    search_hits: list[DocumentSearchHit] = Field(default_factory=list)


class FeedbackCreate(BaseModel):
    user_id: str
    rating: Literal["positive", "negative"]
    comment: str | None = None


class FeedbackRead(BaseModel):
    id: str
    message_id: str
    user_id: str
    rating: str
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsRead(BaseModel):
    organization_id: str
    employee_count: int
    document_count: int
    indexed_document_count: int
    chat_session_count: int
    question_count: int
    popular_questions: list[str]
    sensitive_restrictions: str | None


class RestrictionUpdate(BaseModel):
    sensitive_restrictions: str = Field(..., description="Noi dung nhay cam nhan vien khong nen hoi.")


class UserSettingsUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    public_profile: str | None = None
    avatar_url: str | None = None
    default_organization_id: str | None = None
    locale: str | None = Field(None, examples=["vi", "en"])
    timezone: str | None = Field(None, examples=["Asia/Saigon"])


class OrganizationSettingsRead(BaseModel):
    organization: OrganizationRead
    settings: dict[str, Any]


class OrganizationSettingsUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    industry: str | None = None
    description: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)


class BillingCheckoutCreate(BaseModel):
    created_by_user_id: str
    plan: Literal["free", "business", "enterprise"]
    amount: int = Field(0, ge=0)
    currency: str = Field("VND", min_length=3, max_length=10)
    provider: Literal["manual", "stripe", "momo", "vnpay"] = "manual"
    provider_reference: str | None = None


class BillingRecordRead(BaseModel):
    id: str
    organization_id: str
    created_by_user_id: str | None
    plan: str
    status: str
    amount: int
    currency: str
    provider: str
    provider_reference: str | None
    created_at: datetime


class BillingSummary(BaseModel):
    organization_id: str
    billing_plan: str
    billing_status: str
    records: list[BillingRecordRead]


class BillingStatusUpdate(BaseModel):
    status: Literal["pending", "paid", "failed", "refunded", "canceled"]
    provider_reference: str | None = None


class AuthRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)


class AuthLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleOAuthExchange(BaseModel):
    code: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1, max_length=500)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserRead


class NotificationCreate(BaseModel):
    user_id: str
    organization_id: str | None = None
    notification_type: Literal["system", "organization"] = "system"
    title: str
    content: str | None = None
    action_url: str | None = None


class NotificationRead(BaseModel):
    id: str
    user_id: str
    organization_id: str | None
    notification_type: str
    title: str
    content: str | None
    action_url: str | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PermissionCatalog(BaseModel):
    roles: dict[str, list[str]]
    permissions: dict[str, str]
