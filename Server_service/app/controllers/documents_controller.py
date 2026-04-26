import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import messages, models
from app.database import get_db
from app.dtos import document_dto
from app.entities import database as db_entities
from app.entities.document import DocumentPipelineEntity, DocumentPreviewEntity, DocumentSearchResultEntity
from app.repositories import documents_repository
from app.repositories.common import parse_json_dict, parse_json_list
from app.services.document_preview import build_preview_payload, extract_document_text
from app.services.search_service import index_document, query_documents
from app.services.storage import get_file_from_minio, upload_file_to_minio

router = APIRouter()


def _get_membership(org_id: str, user_id: str, db: Session) -> db_entities.OrganizationMember | None:
    return (
        db.query(db_entities.OrganizationMember)
        .filter(
            db_entities.OrganizationMember.organization_id == org_id,
            db_entities.OrganizationMember.user_id == user_id,
            db_entities.OrganizationMember.status == "active",
        )
        .first()
    )


def _require_permission(org_id: str, user_id: str, permission: str, db: Session) -> db_entities.OrganizationMember:
    membership = _get_membership(org_id, user_id, db)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
    permissions = parse_json_list(membership.permissions)
    if membership.role != "admin" and permission not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
    return membership


def _get_document_or_404(document_id: str, db: Session) -> db_entities.Document:
    document = documents_repository.get_document(document_id, db)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.DOCUMENT_NOT_FOUND)
    return document


def _mark_document_indexed(
    document: db_entities.Document,
    *,
    actor_user_id: str,
    content_text: str | None,
    db: Session,
) -> None:
    document.status = "completed"
    document.chunk_count = "1"
    index_document(document, content_text=content_text)
    documents_repository.create_pipeline_event(
        organization_id=document.organization_id,
        document_id=document.id,
        actor_user_id=actor_user_id,
        stage="indexing",
        status="completed",
        message=messages.DOCUMENT_INDEXED,
        db=db,
    )


@router.post(
    "/organizations/{org_id}/documents",
    response_model=models.DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Dang ky tai lieu va bat dau pipeline ingest",
)
def create_document(org_id: str, payload: models.DocumentCreate, db: Session = Depends(get_db)) -> models.DocumentRead:
    if not documents_repository.get_organization(org_id, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)
    _require_permission(org_id, payload.uploaded_by_user_id, "upload_documents", db)
    document = documents_repository.create_document(
        org_id=org_id,
        uploaded_by_user_id=payload.uploaded_by_user_id,
        file_name=payload.file_name,
        source_url=payload.source_url,
        metadata_json=json.dumps(payload.metadata),
        vector_index=f"org-{org_id}-documents",
        db=db,
    )
    documents_repository.create_pipeline_event(
        organization_id=org_id,
        document_id=document.id,
        actor_user_id=payload.uploaded_by_user_id,
        stage="ingest",
        status="processing",
        message="Tai lieu da duoc ghi nhan, dang index vao Search-service.",
        db=db,
    )
    _mark_document_indexed(document, actor_user_id=payload.uploaded_by_user_id, content_text=None, db=db)
    documents_repository.save_document(db)
    documents_repository.refresh_document(document, db)
    return document_dto.to_document_model(document)


@router.post(
    "/organizations/{org_id}/documents/upload",
    response_model=models.DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Upload file len MinIO va dang ky metadata tai lieu",
)
def upload_document_file(
    org_id: str,
    acting_user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> models.DocumentRead:
    if not documents_repository.get_organization(org_id, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)
    uploader = documents_repository.get_user(acting_user_id, db)
    if not uploader:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
    _require_permission(org_id, acting_user_id, "upload_documents", db)

    file.file.seek(0)
    file_bytes = file.file.read()
    file.file.seek(0)
    extracted_text = extract_document_text(file.filename or "document", file_bytes)
    stored_object = upload_file_to_minio(org_id, file)

    metadata = {
        "uploaded_by_email": uploader.email,
        "content_type": stored_object.content_type,
        "storage_provider": "minio",
        "bucket": stored_object.bucket,
        "object_key": stored_object.object_key,
        "content_text": extracted_text or "",
    }
    document = documents_repository.create_document(
        org_id=org_id,
        uploaded_by_user_id=acting_user_id,
        file_name=file.filename or "document",
        source_url=stored_object.source_url,
        metadata_json=json.dumps(metadata),
        vector_index=f"org-{org_id}-documents",
        db=db,
    )
    documents_repository.create_pipeline_event(
        organization_id=org_id,
        document_id=document.id,
        actor_user_id=acting_user_id,
        stage="upload",
        status="processing",
        message="File da duoc luu trong MinIO va metadata da duoc ghi vao database.",
        db=db,
    )
    _mark_document_indexed(document, actor_user_id=acting_user_id, content_text=extracted_text, db=db)
    documents_repository.save_document(db)
    documents_repository.refresh_document(document, db)
    return document_dto.to_document_model(document)


@router.get("/organizations/{org_id}/documents", response_model=list[models.DocumentRead], tags=["Documents"], summary="Lay danh sach tai lieu cua to chuc")
def list_documents(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents."),
    status_filter: str | None = Query(None, alias="status", description="processing/completed/failed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.DocumentRead]:
    _require_permission(org_id, acting_user_id, "read_documents", db)
    return document_dto.to_document_models(documents_repository.list_documents(org_id, status_filter, skip, limit, db))


@router.post("/organizations/{org_id}/documents/search", response_model=list[models.DocumentSearchHit], tags=["Documents"], summary="Tim tai lieu trong Elasticsearch")
def search_documents(
    org_id: str,
    payload: models.DocumentSearchRequest,
    db: Session = Depends(get_db),
) -> list[models.DocumentSearchHit]:
    _require_permission(org_id, payload.user_id, "read_documents", db)
    try:
        hits = query_documents(f"org-{org_id}-documents", payload.query, size=payload.size)
    except HTTPException:
        hits = []
    return document_dto.to_document_search_hit_models(DocumentSearchResultEntity(hits=hits))


@router.get("/documents/{document_id}/pipeline", response_model=models.DocumentPipeline, tags=["Documents"], summary="Xem trang thai pipeline cua tai lieu")
def get_document_pipeline(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    db: Session = Depends(get_db),
) -> models.DocumentPipeline:
    document = _get_document_or_404(document_id, db)
    _require_permission(document.organization_id, acting_user_id, "read_documents", db)
    entity = DocumentPipelineEntity(document=document, events=documents_repository.list_pipeline_events(document_id, db))
    return document_dto.to_document_pipeline_model(entity)


@router.patch("/documents/{document_id}/status", response_model=models.DocumentRead, tags=["Documents"], summary="Cap nhat pipeline/status tai lieu")
def update_document_status(
    document_id: str,
    payload: models.DocumentStatusPatch,
    acting_user_id: str = Query(..., description="Can quyen upload_documents."),
    db: Session = Depends(get_db),
) -> models.DocumentRead:
    document = _get_document_or_404(document_id, db)
    _require_permission(document.organization_id, acting_user_id, "upload_documents", db)
    documents_repository.update_document_status_fields(
        document,
        status_value=payload.status,
        chunk_count=payload.chunk_count,
        embedding_model=payload.embedding_model,
        vector_index=payload.vector_index,
    )
    if payload.stage:
        documents_repository.create_pipeline_event(
            organization_id=document.organization_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage=payload.stage,
            status=payload.status or document.status,
            message=payload.message,
            db=db,
        )
    documents_repository.save_document(db)
    documents_repository.refresh_document(document, db)
    return document_dto.to_document_model(document)


@router.get("/documents/{document_id}/content", tags=["Documents"], summary="Doc noi dung file goc cua tai lieu")
def get_document_content(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    db: Session = Depends(get_db),
):
    document = _get_document_or_404(document_id, db)
    _require_permission(document.organization_id, acting_user_id, "read_documents", db)
    metadata = parse_json_dict(document.metadata_json)
    bucket = metadata.get("bucket")
    object_key = metadata.get("object_key")
    if not bucket or not object_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.DOCUMENT_STORAGE_METADATA_INVALID)
    minio_response = get_file_from_minio(bucket, object_key)
    content_type = metadata.get("content_type") or "application/octet-stream"
    headers = {
        "Content-Disposition": f'inline; filename="{document.file_name}"',
        "Cache-Control": "private, max-age=60",
    }
    return StreamingResponse(minio_response["Body"], media_type=content_type, headers=headers)


@router.get("/documents/{document_id}/preview", response_model=models.DocumentPreviewRead, tags=["Documents"], summary="Lay noi dung preview cua tai lieu")
def get_document_preview(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    db: Session = Depends(get_db),
) -> models.DocumentPreviewRead:
    document = _get_document_or_404(document_id, db)
    _require_permission(document.organization_id, acting_user_id, "read_documents", db)
    metadata = parse_json_dict(document.metadata_json)
    bucket = metadata.get("bucket")
    object_key = metadata.get("object_key")
    if not bucket or not object_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.DOCUMENT_STORAGE_METADATA_INVALID)
    minio_response = get_file_from_minio(bucket, object_key)
    file_bytes = minio_response["Body"].read()
    preview = build_preview_payload(document.file_name, file_bytes)
    entity = DocumentPreviewEntity(document=document, kind=preview.kind, content=preview.content, message=preview.message)
    return document_dto.to_document_preview_model(entity)
