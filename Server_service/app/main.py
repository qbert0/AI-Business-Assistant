import json
import os
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Iterable
from urllib.parse import quote

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import Base, engine, get_db

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover - allows running without optional MinIO deps in limited dev setups
    boto3 = None
    BotoCoreError = ClientError = Exception
from app import models, schemas


DEFAULT_USER_PERMISSIONS = ["chat_advisory", "read_documents"]
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "business-documents")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
bearer_scheme = HTTPBearer()
ADMIN_PERMISSIONS = [
    "access_org_settings",
    "chat_advisory",
    "read_documents",
    "view_employees",
    "upload_documents",
    "view_analytics",
    "edit_sensitive_restrictions",
    "delete_chat_sessions",
]
PERMISSION_DESCRIPTIONS = {
    "access_org_settings": "Truy cap cai dat to chuc.",
    "chat_advisory": "Dung chat tu van theo tai lieu noi bo.",
    "read_documents": "Doc danh sach va metadata tai lieu.",
    "view_employees": "Xem danh sach nhan vien.",
    "upload_documents": "Upload va kich hoat pipeline xu ly tai lieu.",
    "view_analytics": "Xem dashboard phan tich to chuc.",
    "edit_sensitive_restrictions": "Sua cau hinh han che noi dung nhay cam.",
    "delete_chat_sessions": "Xoa doan chat.",
}

tags_metadata = [
    {"name": "System", "description": "Kiem tra trang thai server va danh muc kha nang he thong."},
    {"name": "Auth", "description": "Dang ky, dang nhap va xac thuc Bearer JWT."},
    {"name": "Users", "description": "Tai khoan nguoi dung ca nhan dung cho auth, membership va notification."},
    {"name": "Organizations", "description": "Quan ly cong ty/workspace, danh sach to chuc va dashboard tong quan."},
    {"name": "Members & RBAC", "description": "Quan ly nhan vien, role admin/user va permission theo tung to chuc."},
    {"name": "Documents", "description": "Upload metadata tai lieu, theo doi chunking, embedding va indexing."},
    {"name": "Chat", "description": "Chat tu van theo context ca nhan hoac to chuc, kem citation va feedback."},
    {"name": "Analytics", "description": "Thong ke su dung, cau hoi pho bien va han che noi dung nhay cam."},
    {"name": "Settings", "description": "Cai dat ca nhan va cai dat to chuc."},
    {"name": "Billing", "description": "Goi thanh toan, checkout mock va cap nhat trang thai thanh toan."},
    {"name": "Notifications", "description": "Thong bao co link hanh dong cho user va to chuc."},
]
models.Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="AI Business Assistant API",
    description=(
        "Backend API cho AI Business Assistant. He thong ho tro nguoi dung ca nhan, "
        "to chuc, nhan vien, RBAC, quan ly tai lieu, pipeline multi-agent, chat RAG, "
        "analytics va notification. Mo Swagger UI tai `/docs`."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={"name": "AI Business Assistant"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)



def get_minio_client():
    if not MINIO_ENDPOINT:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MinIO endpoint chua duoc cau hinh.")
    if boto3 is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Thu vien boto3 chua duoc cai dat.")
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        use_ssl=MINIO_SECURE,
    )


def ensure_minio_bucket(client) -> None:
    try:
        client.head_bucket(Bucket=MINIO_BUCKET)
    except ClientError:
        client.create_bucket(Bucket=MINIO_BUCKET)


def upload_file_to_minio(org_id: str, file: UploadFile) -> str:
    client = get_minio_client()
    ensure_minio_bucket(client)
    safe_name = quote(file.filename or "document", safe="._-")
    object_key = f"organizations/{org_id}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{safe_name}"
    try:
        file.file.seek(0)
        client.upload_fileobj(
            file.file,
            MINIO_BUCKET,
            object_key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Khong upload duoc file len MinIO: {exc}")
    return f"s3://{MINIO_BUCKET}/{object_key}"


def parse_json_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def parse_json_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def dump_schema(schema, **kwargs) -> dict:
    if hasattr(schema, "model_dump"):
        return schema.model_dump(**kwargs)
    return schema.dict(**kwargs)


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"pbkdf2_sha256$200000${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, expected)


def create_access_token(user: models.User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    header = {"typ": "JWT", "alg": JWT_ALGORITHM}
    payload = {"sub": user.id, "email": user.email, "exp": int(expires_at.timestamp())}
    signing_input = ".".join(
        [
            b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(JWT_SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{b64url_encode(signature)}"


def decode_access_token(token: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        provided_signature = b64url_decode(signature_b64)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("Invalid signature")
        header = json.loads(b64url_decode(header_b64))
        if header.get("alg") != JWT_ALGORITHM:
            raise ValueError("Invalid algorithm")
        payload = json.loads(b64url_decode(payload_b64))
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Expired token")
        return payload
    except (ValueError, json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Khong xac thuc duoc JWT.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def permissions_for_role(role: str, permissions: Iterable[str] | None = None) -> list[str]:
    if role == "admin":
        return ADMIN_PERMISSIONS
    return list(permissions) if permissions is not None else DEFAULT_USER_PERMISSIONS


def serialize_member(member: models.OrganizationMember) -> schemas.MemberRead:
    return schemas.MemberRead(
        id=member.id,
        user_id=member.user_id,
        organization_id=member.organization_id,
        role=member.role,
        permissions=parse_json_list(member.permissions),
        status=member.status,
        joined_at=member.joined_at,
        user=member.user,
    )


def serialize_document(document: models.Document) -> schemas.DocumentRead:
    return schemas.DocumentRead(
        id=document.id,
        organization_id=document.organization_id,
        uploaded_by_user_id=document.uploaded_by_user_id,
        file_name=document.file_name,
        source_url=document.source_url,
        status=document.status,
        chunk_count=int(document.chunk_count or 0),
        embedding_model=document.embedding_model,
        vector_index=document.vector_index,
        metadata=parse_json_dict(document.metadata_json),
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def serialize_billing_record(record: models.BillingRecord) -> schemas.BillingRecordRead:
    return schemas.BillingRecordRead(
        id=record.id,
        organization_id=record.organization_id,
        created_by_user_id=record.created_by_user_id,
        plan=record.plan,
        status=record.status,
        amount=int(record.amount or 0),
        currency=record.currency,
        provider=record.provider,
        provider_reference=record.provider_reference,
        created_at=record.created_at,
    )


def serialize_message(message: models.ChatMessage) -> schemas.ChatMessageRead:
    return schemas.ChatMessageRead(
        id=message.id,
        session_id=message.session_id,
        sender_type=message.sender_type,
        content=message.content,
        citations=[schemas.Citation(**item) for item in parse_json_list(message.citations_json)],
        created_at=message.created_at,
    )


def get_user_or_404(db: Session, user_id: str) -> models.User:
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User khong ton tai.")
    return user


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> models.User:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Khong xac thuc duoc JWT.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(models.User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Khong xac thuc duoc JWT.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_org_or_404(db: Session, org_id: str) -> models.Organization:
    org = db.get(models.Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="To chuc khong ton tai.")
    return org


def get_membership(db: Session, org_id: str, user_id: str) -> models.OrganizationMember | None:
    return (
        db.query(models.OrganizationMember)
        .filter(
            models.OrganizationMember.organization_id == org_id,
            models.OrganizationMember.user_id == user_id,
            models.OrganizationMember.status == "active",
        )
        .first()
    )


def require_permission(db: Session, org_id: str, user_id: str, permission: str) -> models.OrganizationMember:
    membership = get_membership(db, org_id, user_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User khong thuoc to chuc nay.")
    permissions = parse_json_list(membership.permissions)
    if membership.role != "admin" and permission not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
    return membership


@app.get("/", response_model=schemas.ApiInfo, tags=["System"], summary="Thong tin API va link Swagger")
def root() -> schemas.ApiInfo:
    return schemas.ApiInfo(
        name="AI Business Assistant API",
        version="1.0.0",
        docs_url="/docs",
        health_url="/health",
        capabilities=[
            "Personal workspace",
            "Organization workspace",
            "JWT authentication",
            "RBAC admin/user",
            "Document ingestion pipeline",
            "Organization-scoped advisory chat",
            "Analytics and sensitive-content restrictions",
            "Settings and billing",
            "Actionable notifications",
        ],
    )


@app.get("/health", tags=["System"], summary="Kiem tra server dang chay")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/permissions", response_model=schemas.PermissionCatalog, tags=["Members & RBAC"], summary="Danh muc role va permission")
def permission_catalog() -> schemas.PermissionCatalog:
    return schemas.PermissionCatalog(
        roles={"admin": ADMIN_PERMISSIONS, "user": DEFAULT_USER_PERMISSIONS},
        permissions=PERMISSION_DESCRIPTIONS,
    )


@app.post("/auth/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"], summary="Dang ky va nhan JWT")
def register(payload: schemas.AuthRegister, db: Session = Depends(get_db)) -> schemas.TokenResponse:
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email da duoc dang ky.")
    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.TokenResponse(
        access_token=create_access_token(user),
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@app.post("/auth/login", response_model=schemas.TokenResponse, tags=["Auth"], summary="Dang nhap bang email/password va nhan JWT")
def login(payload: schemas.AuthLogin, db: Session = Depends(get_db)) -> schemas.TokenResponse:
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoac mat khau khong dung.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tai khoan da bi vo hieu hoa.")
    return schemas.TokenResponse(
        access_token=create_access_token(user),
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@app.get("/auth/me", response_model=schemas.UserRead, tags=["Auth"], summary="Lay user hien tai tu Bearer JWT")
def auth_me(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


@app.post("/users", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED, tags=["Users"], summary="Tao user moi")
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)) -> models.User:
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email da duoc dang ky.")
    user = models.User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password) if payload.password else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=list[schemas.UserRead], tags=["Users"], summary="Lay danh sach user")
def list_users(
    search: str | None = Query(None, description="Tim theo email hoac ten."),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.User]:
    query = db.query(models.User)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(models.User.email.like(like), models.User.full_name.like(like)))
    return query.order_by(models.User.created_at.desc()).offset(skip).limit(limit).all()


@app.get("/users/{user_id}", response_model=schemas.UserRead, tags=["Users"], summary="Lay chi tiet user")
def get_user(user_id: str, db: Session = Depends(get_db)) -> models.User:
    return get_user_or_404(db, user_id)


@app.post(
    "/organizations",
    response_model=schemas.OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Organizations"],
    summary="Tao to chuc moi va gan owner lam admin",
)
def create_organization(payload: schemas.OrganizationCreate, db: Session = Depends(get_db)) -> models.Organization:
    get_user_or_404(db, payload.owner_user_id)
    org = models.Organization(name=payload.name, industry=payload.industry, description=payload.description)
    db.add(org)
    db.flush()
    member = models.OrganizationMember(
        user_id=payload.owner_user_id,
        organization_id=org.id,
        role="admin",
        permissions=json.dumps(ADMIN_PERMISSIONS),
        status="active",
    )
    db.add(member)
    db.commit()
    db.refresh(org)
    return org


@app.get("/organizations", response_model=list[schemas.OrganizationRead], tags=["Organizations"], summary="Lay danh sach to chuc")
def list_organizations(
    search: str | None = Query(None, description="Tim theo ten, nganh nghe hoac mo ta."),
    user_id: str | None = Query(None, description="Neu truyen, chi lay to chuc user dang tham gia."),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.Organization]:
    query = db.query(models.Organization)
    if user_id:
        query = query.join(models.OrganizationMember).filter(models.OrganizationMember.user_id == user_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.Organization.name.like(like),
                models.Organization.industry.like(like),
                models.Organization.description.like(like),
            )
        )
    return query.order_by(models.Organization.created_at.desc()).offset(skip).limit(limit).all()


@app.get("/organizations/{org_id}", response_model=schemas.OrganizationRead, tags=["Organizations"], summary="Lay chi tiet to chuc")
def get_organization(org_id: str, db: Session = Depends(get_db)) -> models.Organization:
    return get_org_or_404(db, org_id)


@app.patch("/organizations/{org_id}", response_model=schemas.OrganizationRead, tags=["Organizations"], summary="Cap nhat thong tin to chuc")
def update_organization(
    org_id: str,
    payload: schemas.OrganizationUpdate,
    acting_user_id: str = Query(..., description="User thuc hien thao tac, can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.Organization:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    for field, value in dump_schema(payload, exclude_unset=True).items():
        setattr(org, field, value)
    db.commit()
    db.refresh(org)
    return org


@app.get("/organizations/{org_id}/dashboard", response_model=schemas.OrganizationDashboard, tags=["Organizations"], summary="Tong quan to chuc")
def organization_dashboard(
    org_id: str,
    acting_user_id: str = Query(..., description="User dang xem dashboard, phai thuoc to chuc."),
    db: Session = Depends(get_db),
) -> schemas.OrganizationDashboard:
    org = get_org_or_404(db, org_id)
    if not get_membership(db, org_id, acting_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User khong thuoc to chuc nay.")
    document_count = db.query(models.Document).filter(models.Document.organization_id == org_id).count()
    return schemas.OrganizationDashboard(
        organization=org,
        employee_count=db.query(models.OrganizationMember).filter(models.OrganizationMember.organization_id == org_id).count(),
        document_count=document_count,
        indexed_document_count=db.query(models.Document)
        .filter(models.Document.organization_id == org_id, models.Document.status == "completed")
        .count(),
        chat_session_count=db.query(models.ChatSession).filter(models.ChatSession.organization_id == org_id).count(),
        suggested_questions=[
            "Chinh sach nghi phep cua cong ty la gi?",
            "Quy trinh phe duyet chi phi noi bo nhu the nao?",
            "Nhan vien moi can doc tai lieu nao dau tien?",
        ],
    )


@app.post(
    "/organizations/{org_id}/members",
    response_model=schemas.MemberRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Members & RBAC"],
    summary="Them nhan vien vao to chuc",
)
def add_member(
    org_id: str,
    payload: schemas.MemberCreate,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> schemas.MemberRead:
    get_org_or_404(db, org_id)
    get_user_or_404(db, payload.user_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    if get_membership(db, org_id, payload.user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User da thuoc to chuc.")
    member = models.OrganizationMember(
        user_id=payload.user_id,
        organization_id=org_id,
        role=payload.role,
        permissions=json.dumps(permissions_for_role(payload.role, payload.permissions)),
        status=payload.status,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    member = db.query(models.OrganizationMember).options(joinedload(models.OrganizationMember.user)).get(member.id)
    return serialize_member(member)


@app.get("/organizations/{org_id}/members", response_model=list[schemas.MemberRead], tags=["Members & RBAC"], summary="Lay danh sach nhan vien")
def list_members(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen view_employees."),
    search: str | None = Query(None, description="Tim theo ten hoac email."),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[schemas.MemberRead]:
    require_permission(db, org_id, acting_user_id, "view_employees")
    query = (
        db.query(models.OrganizationMember)
        .options(joinedload(models.OrganizationMember.user))
        .join(models.User)
        .filter(models.OrganizationMember.organization_id == org_id)
    )
    if search:
        like = f"%{search}%"
        query = query.filter(or_(models.User.email.like(like), models.User.full_name.like(like)))
    members = query.order_by(models.OrganizationMember.joined_at.desc()).offset(skip).limit(limit).all()
    return [serialize_member(member) for member in members]


@app.patch("/organizations/{org_id}/members/{member_id}", response_model=schemas.MemberRead, tags=["Members & RBAC"], summary="Cap nhat role/permission nhan vien")
def update_member(
    org_id: str,
    member_id: str,
    payload: schemas.MemberPatch,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> schemas.MemberRead:
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    member = (
        db.query(models.OrganizationMember)
        .options(joinedload(models.OrganizationMember.user))
        .filter(models.OrganizationMember.id == member_id, models.OrganizationMember.organization_id == org_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhan vien khong ton tai.")
    if payload.role is not None:
        member.role = payload.role
        if payload.permissions is None:
            member.permissions = json.dumps(permissions_for_role(payload.role))
    if payload.permissions is not None:
        member.permissions = json.dumps(permissions_for_role(payload.role or member.role, payload.permissions))
    if payload.status is not None:
        member.status = payload.status
    db.commit()
    db.refresh(member)
    return serialize_member(member)


@app.delete("/organizations/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Members & RBAC"], summary="Xoa nhan vien khoi to chuc")
def delete_member(
    org_id: str,
    member_id: str,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> None:
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    member = (
        db.query(models.OrganizationMember)
        .filter(models.OrganizationMember.id == member_id, models.OrganizationMember.organization_id == org_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nhan vien khong ton tai.")
    db.delete(member)
    db.commit()


@app.delete("/organizations/{org_id}/membership", status_code=status.HTTP_204_NO_CONTENT, tags=["Members & RBAC"], summary="Roi khoi to chuc")
def leave_organization(
    org_id: str,
    acting_user_id: str = Query(..., description="User muon roi khoi to chuc."),
    db: Session = Depends(get_db),
) -> None:
    member = (
        db.query(models.OrganizationMember)
        .filter(
            models.OrganizationMember.organization_id == org_id,
            models.OrganizationMember.user_id == acting_user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User khong thuoc to chuc nay.")
    if member.role == "admin":
        active_admin_count = (
            db.query(models.OrganizationMember)
            .filter(
                models.OrganizationMember.organization_id == org_id,
                models.OrganizationMember.role == "admin",
                models.OrganizationMember.status == "active",
            )
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cuoi cung khong the roi to chuc.")
    db.delete(member)
    db.commit()


@app.post(
    "/organizations/{org_id}/documents",
    response_model=schemas.DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Dang ky tai lieu va bat dau pipeline ingest",
)
def create_document(org_id: str, payload: schemas.DocumentCreate, db: Session = Depends(get_db)) -> schemas.DocumentRead:
    get_org_or_404(db, org_id)
    require_permission(db, org_id, payload.uploaded_by_user_id, "upload_documents")
    document = models.Document(
        organization_id=org_id,
        uploaded_by_user_id=payload.uploaded_by_user_id,
        file_name=payload.file_name,
        source_url=payload.source_url,
        vector_index=f"org-{org_id}-documents",
        metadata_json=json.dumps(payload.metadata),
    )
    db.add(document)
    db.flush()
    db.add(
        models.PipelineEvent(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=payload.uploaded_by_user_id,
            stage="ingest",
            status="processing",
            message="Tai lieu da duoc ghi nhan, cho chunking va embedding.",
        )
    )
    db.commit()
    db.refresh(document)
    return serialize_document(document)




@app.post(
    "/organizations/{org_id}/documents/upload",
    response_model=schemas.DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Upload file len MinIO va dang ky metadata tai lieu",
)
def upload_document_file(
    org_id: str,
    acting_user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> schemas.DocumentRead:
    get_org_or_404(db, org_id)
    uploader = get_user_or_404(db, acting_user_id)
    require_permission(db, org_id, acting_user_id, "upload_documents")
    source_url = upload_file_to_minio(org_id, file)
    document = models.Document(
        organization_id=org_id,
        uploaded_by_user_id=acting_user_id,
        file_name=file.filename or "document",
        source_url=source_url,
        vector_index=f"org-{org_id}-documents",
        metadata_json=json.dumps(
            {
                "uploaded_by_email": uploader.email,
                "content_type": file.content_type,
                "storage_provider": "minio",
                "bucket": MINIO_BUCKET,
            }
        ),
    )
    db.add(document)
    db.flush()
    db.add(
        models.PipelineEvent(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage="upload",
            status="processing",
            message="File da duoc luu trong MinIO va metadata da duoc ghi vao database.",
        )
    )
    db.commit()
    db.refresh(document)
    return serialize_document(document)

@app.get("/organizations/{org_id}/documents", response_model=list[schemas.DocumentRead], tags=["Documents"], summary="Lay danh sach tai lieu cua to chuc")
def list_documents(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents."),
    status_filter: str | None = Query(None, alias="status", description="processing/completed/failed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[schemas.DocumentRead]:
    require_permission(db, org_id, acting_user_id, "read_documents")
    query = db.query(models.Document).filter(models.Document.organization_id == org_id)
    if status_filter:
        query = query.filter(models.Document.status == status_filter)
    documents = query.order_by(models.Document.created_at.desc()).offset(skip).limit(limit).all()
    return [serialize_document(document) for document in documents]


@app.get("/documents/{document_id}/pipeline", response_model=schemas.DocumentPipeline, tags=["Documents"], summary="Xem trang thai pipeline cua tai lieu")
def get_document_pipeline(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    db: Session = Depends(get_db),
) -> schemas.DocumentPipeline:
    document = db.get(models.Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tai lieu khong ton tai.")
    require_permission(db, document.organization_id, acting_user_id, "read_documents")
    events = (
        db.query(models.PipelineEvent)
        .filter(models.PipelineEvent.document_id == document_id)
        .order_by(models.PipelineEvent.created_at.asc())
        .all()
    )
    return schemas.DocumentPipeline(document=serialize_document(document), events=events)


@app.patch("/documents/{document_id}/status", response_model=schemas.DocumentRead, tags=["Documents"], summary="Cap nhat pipeline/status tai lieu")
def update_document_status(
    document_id: str,
    payload: schemas.DocumentStatusPatch,
    acting_user_id: str = Query(..., description="Can quyen upload_documents."),
    db: Session = Depends(get_db),
) -> schemas.DocumentRead:
    document = db.get(models.Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tai lieu khong ton tai.")
    require_permission(db, document.organization_id, acting_user_id, "upload_documents")
    if payload.status is not None:
        document.status = payload.status
    if payload.chunk_count is not None:
        document.chunk_count = str(payload.chunk_count)
    if payload.embedding_model is not None:
        document.embedding_model = payload.embedding_model
    if payload.vector_index is not None:
        document.vector_index = payload.vector_index
    if payload.stage:
        db.add(
            models.PipelineEvent(
                organization_id=document.organization_id,
                document_id=document.id,
                actor_user_id=acting_user_id,
                stage=payload.stage,
                status=payload.status or document.status,
                message=payload.message,
            )
        )
    db.commit()
    db.refresh(document)
    return serialize_document(document)


@app.get("/organizations/{org_id}/chat/suggestions", response_model=list[str], tags=["Chat"], summary="Lay goi y cau hoi theo to chuc")
def chat_suggestions(org_id: str, acting_user_id: str, db: Session = Depends(get_db)) -> list[str]:
    require_permission(db, org_id, acting_user_id, "chat_advisory")
    return [
        "Thu nhap va phuc loi hien tai gom nhung gi?",
        "Chinh sach nghi phep ap dung ra sao?",
        "Quy trinh noi bo nao lien quan den nhan vien moi?",
    ]


@app.get("/organizations/{org_id}/chat/sessions", response_model=list[schemas.ChatSessionRead], tags=["Chat"], summary="Lay chat history theo context to chuc")
def list_chat_sessions(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen chat_advisory."),
    db: Session = Depends(get_db),
) -> list[models.ChatSession]:
    require_permission(db, org_id, acting_user_id, "chat_advisory")
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.organization_id == org_id, models.ChatSession.user_id == acting_user_id)
        .order_by(models.ChatSession.updated_at.desc())
        .all()
    )


@app.post("/organizations/{org_id}/chat/sessions", response_model=schemas.ChatSessionRead, status_code=status.HTTP_201_CREATED, tags=["Chat"], summary="Tao chat session rong")
def create_chat_session(org_id: str, payload: schemas.ChatSessionCreate, db: Session = Depends(get_db)) -> models.ChatSession:
    require_permission(db, org_id, payload.user_id, "chat_advisory")
    session = models.ChatSession(
        organization_id=org_id,
        user_id=payload.user_id,
        context_type=payload.context_type,
        title=payload.title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@app.get("/chat/sessions/{session_id}/messages", response_model=list[schemas.ChatMessageRead], tags=["Chat"], summary="Lay message trong mot chat session")
def list_chat_messages(
    session_id: str,
    acting_user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> list[schemas.ChatMessageRead]:
    session = db.get(models.ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session khong ton tai.")
    if session.organization_id:
        require_permission(db, session.organization_id, acting_user_id, "chat_advisory")
    elif session.user_id != acting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc xem chat cua user khac.")
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    return [serialize_message(message) for message in messages]


@app.post("/organizations/{org_id}/chat/ask", response_model=schemas.ChatAnswer, tags=["Chat"], summary="Hoi dap theo tai lieu noi bo to chuc")
def ask_chat(org_id: str, payload: schemas.ChatAsk, db: Session = Depends(get_db)) -> schemas.ChatAnswer:
    require_permission(db, org_id, payload.user_id, "chat_advisory")
    session = db.get(models.ChatSession, payload.session_id) if payload.session_id else None
    if session and session.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session khong thuoc to chuc nay.")
    if not session:
        title = payload.question[:80]
        session = models.ChatSession(organization_id=org_id, user_id=payload.user_id, context_type="organization", title=title)
        db.add(session)
        db.flush()

    documents = (
        db.query(models.Document)
        .filter(models.Document.organization_id == org_id, models.Document.status == "completed")
        .order_by(models.Document.updated_at.desc())
        .limit(3)
        .all()
    )
    citations = [
        {"document_id": item.id, "file_name": item.file_name, "source_url": item.source_url}
        for item in documents
    ]
    answer = (
        "Day la cau tra loi mau cua AI Business Assistant dua tren tai lieu noi bo da index. "
        "Ban co the thay phan citation de kiem chung nguon. Ket noi LLM/RAG that co the duoc gan "
        "vao endpoint nay sau khi pipeline embedding va retrieval san sang."
    )
    user_message = models.ChatMessage(session_id=session.id, sender_type="user", content=payload.question)
    assistant_message = models.ChatMessage(
        session_id=session.id,
        sender_type="ai",
        content=answer,
        citations_json=json.dumps(citations),
    )
    db.add_all([user_message, assistant_message])
    db.commit()
    db.refresh(session)
    db.refresh(user_message)
    db.refresh(assistant_message)
    return schemas.ChatAnswer(
        session=session,
        user_message=serialize_message(user_message),
        assistant_message=serialize_message(assistant_message),
        answer=answer,
        citations=[schemas.Citation(**item) for item in citations],
    )


@app.post("/chat/messages/{message_id}/feedback", response_model=schemas.FeedbackRead, status_code=status.HTTP_201_CREATED, tags=["Chat"], summary="Gui feedback cho cau tra loi")
def create_feedback(message_id: str, payload: schemas.FeedbackCreate, db: Session = Depends(get_db)) -> models.ChatFeedback:
    message = db.get(models.ChatMessage, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message khong ton tai.")
    session = db.get(models.ChatSession, message.session_id)
    if session.organization_id:
        require_permission(db, session.organization_id, payload.user_id, "chat_advisory")
    feedback = models.ChatFeedback(message_id=message_id, user_id=payload.user_id, rating=payload.rating, comment=payload.comment)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


@app.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chat"], summary="Xoa mot doan chat")
def delete_chat_session(
    session_id: str,
    acting_user_id: str = Query(..., description="User thuc hien thao tac xoa."),
    db: Session = Depends(get_db),
) -> None:
    session = db.get(models.ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session khong ton tai.")
    if session.organization_id:
        require_permission(db, session.organization_id, acting_user_id, "delete_chat_sessions")
    elif session.user_id != acting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc xoa chat cua user khac.")
    db.delete(session)
    db.commit()


@app.get("/organizations/{org_id}/analytics", response_model=schemas.AnalyticsRead, tags=["Analytics"], summary="Lay analytics cua to chuc")
def get_analytics(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen view_analytics."),
    db: Session = Depends(get_db),
) -> schemas.AnalyticsRead:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "view_analytics")
    user_messages = (
        db.query(models.ChatMessage)
        .join(models.ChatSession)
        .filter(models.ChatSession.organization_id == org_id, models.ChatMessage.sender_type == "user")
        .order_by(models.ChatMessage.created_at.desc())
        .limit(5)
        .all()
    )
    return schemas.AnalyticsRead(
        organization_id=org_id,
        employee_count=db.query(models.OrganizationMember).filter(models.OrganizationMember.organization_id == org_id).count(),
        document_count=db.query(models.Document).filter(models.Document.organization_id == org_id).count(),
        indexed_document_count=db.query(models.Document)
        .filter(models.Document.organization_id == org_id, models.Document.status == "completed")
        .count(),
        chat_session_count=db.query(models.ChatSession).filter(models.ChatSession.organization_id == org_id).count(),
        question_count=db.query(models.ChatMessage)
        .join(models.ChatSession)
        .filter(models.ChatSession.organization_id == org_id, models.ChatMessage.sender_type == "user")
        .count(),
        popular_questions=[message.content for message in user_messages],
        sensitive_restrictions=org.sensitive_restrictions,
    )


@app.put("/organizations/{org_id}/analytics/restrictions", response_model=schemas.AnalyticsRead, tags=["Analytics"], summary="Cap nhat han che noi dung nhay cam")
def update_restrictions(
    org_id: str,
    payload: schemas.RestrictionUpdate,
    acting_user_id: str = Query(..., description="Can quyen edit_sensitive_restrictions."),
    db: Session = Depends(get_db),
) -> schemas.AnalyticsRead:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "edit_sensitive_restrictions")
    org.sensitive_restrictions = payload.sensitive_restrictions
    db.commit()
    return get_analytics(org_id, acting_user_id, db)


@app.get("/settings/profile", response_model=schemas.UserRead, tags=["Settings"], summary="Lay cai dat ca nhan bang JWT")
def get_my_settings(current_user: models.User = Depends(get_current_user)) -> models.User:
    return current_user


@app.patch("/settings/profile", response_model=schemas.UserRead, tags=["Settings"], summary="Cap nhat cai dat ca nhan bang JWT")
def update_my_settings(
    payload: schemas.UserSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.User:
    for field, value in dump_schema(payload, exclude_unset=True).items():
        if field == "default_organization_id" and value is not None:
            if not get_membership(db, value, current_user.id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="To chuc mac dinh khong hop le.")
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@app.get("/users/{user_id}/settings", response_model=schemas.UserRead, tags=["Settings"], summary="Lay cai dat ca nhan theo user_id")
def get_user_settings(user_id: str, db: Session = Depends(get_db)) -> models.User:
    return get_user_or_404(db, user_id)


@app.patch("/users/{user_id}/settings", response_model=schemas.UserRead, tags=["Settings"], summary="Cap nhat cai dat ca nhan theo user_id")
def update_user_settings(user_id: str, payload: schemas.UserSettingsUpdate, db: Session = Depends(get_db)) -> models.User:
    user = get_user_or_404(db, user_id)
    for field, value in dump_schema(payload, exclude_unset=True).items():
        if field == "default_organization_id" and value is not None:
            if not get_membership(db, value, user.id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="To chuc mac dinh khong hop le.")
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@app.get("/organizations/{org_id}/settings", response_model=schemas.OrganizationSettingsRead, tags=["Settings"], summary="Lay cai dat to chuc")
def get_organization_settings(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> schemas.OrganizationSettingsRead:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    return schemas.OrganizationSettingsRead(organization=org, settings=parse_json_dict(org.settings_json))


@app.patch("/organizations/{org_id}/settings", response_model=schemas.OrganizationSettingsRead, tags=["Settings"], summary="Cap nhat cai dat to chuc")
def update_organization_settings(
    org_id: str,
    payload: schemas.OrganizationSettingsUpdate,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> schemas.OrganizationSettingsRead:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    data = dump_schema(payload, exclude_unset=True)
    settings_patch = data.pop("settings", None)
    for field, value in data.items():
        setattr(org, field, value)
    if settings_patch is not None:
        current_settings = parse_json_dict(org.settings_json)
        current_settings.update(settings_patch)
        org.settings_json = json.dumps(current_settings)
    db.commit()
    db.refresh(org)
    return schemas.OrganizationSettingsRead(organization=org, settings=parse_json_dict(org.settings_json))


@app.get("/organizations/{org_id}/billing", response_model=schemas.BillingSummary, tags=["Billing"], summary="Lay thong tin thanh toan cua to chuc")
def get_billing(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> schemas.BillingSummary:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    records = (
        db.query(models.BillingRecord)
        .filter(models.BillingRecord.organization_id == org_id)
        .order_by(models.BillingRecord.created_at.desc())
        .all()
    )
    return schemas.BillingSummary(
        organization_id=org_id,
        billing_plan=org.billing_plan,
        billing_status=org.billing_status,
        records=[serialize_billing_record(record) for record in records],
    )


@app.post("/organizations/{org_id}/billing/checkout", response_model=schemas.BillingRecordRead, status_code=status.HTTP_201_CREATED, tags=["Billing"], summary="Tao checkout/thanh toan cho goi dich vu")
def create_billing_checkout(
    org_id: str,
    payload: schemas.BillingCheckoutCreate,
    db: Session = Depends(get_db),
) -> schemas.BillingRecordRead:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, payload.created_by_user_id, "access_org_settings")
    record = models.BillingRecord(
        organization_id=org_id,
        created_by_user_id=payload.created_by_user_id,
        plan=payload.plan,
        status="pending",
        amount=str(payload.amount),
        currency=payload.currency,
        provider=payload.provider,
        provider_reference=payload.provider_reference,
    )
    org.billing_plan = payload.plan
    org.billing_status = "pending" if payload.plan != "free" else "active"
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_billing_record(record)


@app.patch("/billing/records/{record_id}", response_model=schemas.BillingRecordRead, tags=["Billing"], summary="Cap nhat trang thai thanh toan")
def update_billing_record(
    record_id: str,
    payload: schemas.BillingStatusUpdate,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings trong to chuc cua billing record."),
    db: Session = Depends(get_db),
) -> schemas.BillingRecordRead:
    record = db.get(models.BillingRecord, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing record khong ton tai.")
    org = get_org_or_404(db, record.organization_id)
    require_permission(db, record.organization_id, acting_user_id, "access_org_settings")
    record.status = payload.status
    if payload.provider_reference is not None:
        record.provider_reference = payload.provider_reference
    if payload.status == "paid":
        org.billing_plan = record.plan
        org.billing_status = "active"
    elif payload.status in {"failed", "canceled"}:
        org.billing_status = payload.status
    db.commit()
    db.refresh(record)
    return serialize_billing_record(record)


@app.post("/notifications", response_model=schemas.NotificationRead, status_code=status.HTTP_201_CREATED, tags=["Notifications"], summary="Tao notification")
def create_notification(payload: schemas.NotificationCreate, db: Session = Depends(get_db)) -> models.Notification:
    get_user_or_404(db, payload.user_id)
    if payload.organization_id:
        get_org_or_404(db, payload.organization_id)
    notification = models.Notification(**dump_schema(payload))
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@app.get("/users/{user_id}/notifications", response_model=list[schemas.NotificationRead], tags=["Notifications"], summary="Lay notification cua user")
def list_notifications(user_id: str, unread_only: bool = False, db: Session = Depends(get_db)) -> list[models.Notification]:
    get_user_or_404(db, user_id)
    query = db.query(models.Notification).filter(models.Notification.user_id == user_id)
    if unread_only:
        query = query.filter(models.Notification.is_read.is_(False))
    return query.order_by(models.Notification.created_at.desc()).all()


@app.patch("/notifications/{notification_id}/read", response_model=schemas.NotificationRead, tags=["Notifications"], summary="Danh dau notification da doc")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db)) -> models.Notification:
    notification = db.get(models.Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification khong ton tai.")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
