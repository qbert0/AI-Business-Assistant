import json

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import messages
from app import models
from app.entities import database as db_entities
from app.entities.document import DocumentPipelineEntity, DocumentSearchResultEntity
from app.repositories.common import get_org_or_404, get_user_or_404, require_permission
from app.services.search_service import index_document, query_documents
from app.services.storage import upload_file_to_minio


def _mark_document_indexed(db: Session, document: db_entities.Document, actor_user_id: str) -> None:
    document.status = "completed"
    document.chunk_count = "1"
    index_document(document)
    db.add(
        db_entities.PipelineEvent(
            organization_id=document.organization_id,
            document_id=document.id,
            actor_user_id=actor_user_id,
            stage="indexing",
            status="completed",
            message=messages.DOCUMENT_INDEXED,
        )
    )


def create_document(org_id: str, payload: models.DocumentCreate, db: Session) -> db_entities.Document:
    get_org_or_404(db, org_id)
    require_permission(db, org_id, payload.uploaded_by_user_id, "upload_documents")
    document = db_entities.Document(
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
        db_entities.PipelineEvent(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=payload.uploaded_by_user_id,
            stage="ingest",
            status="processing",
            message="Tai lieu da duoc ghi nhan, dang index vao Search-service.",
        )
    )
    _mark_document_indexed(db, document, payload.uploaded_by_user_id)
    db.commit()
    db.refresh(document)
    return document


def upload_document_file(org_id: str, acting_user_id: str, file: UploadFile, db: Session) -> db_entities.Document:
    get_org_or_404(db, org_id)
    uploader = get_user_or_404(db, acting_user_id)
    require_permission(db, org_id, acting_user_id, "upload_documents")
    stored_object = upload_file_to_minio(org_id, file)
    document = db_entities.Document(
        organization_id=org_id,
        uploaded_by_user_id=acting_user_id,
        file_name=file.filename or "document",
        source_url=stored_object.source_url,
        vector_index=f"org-{org_id}-documents",
        metadata_json=json.dumps(
            {
                "uploaded_by_email": uploader.email,
                "content_type": stored_object.content_type,
                "storage_provider": "minio",
                "bucket": stored_object.bucket,
                "object_key": stored_object.object_key,
            }
        ),
    )
    db.add(document)
    db.flush()
    db.add(
        db_entities.PipelineEvent(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage="upload",
            status="processing",
            message="File da duoc luu trong MinIO va metadata da duoc ghi vao database.",
        )
    )
    _mark_document_indexed(db, document, acting_user_id)
    db.commit()
    db.refresh(document)
    return document


def list_documents(
    org_id: str,
    acting_user_id: str,
    status_filter: str | None,
    skip: int,
    limit: int,
    db: Session,
) -> list[db_entities.Document]:
    require_permission(db, org_id, acting_user_id, "read_documents")
    query = db.query(db_entities.Document).filter(db_entities.Document.organization_id == org_id)
    if status_filter:
        query = query.filter(db_entities.Document.status == status_filter)
    return query.order_by(db_entities.Document.created_at.desc()).offset(skip).limit(limit).all()


def search_documents(org_id: str, payload: models.DocumentSearchRequest, db: Session) -> DocumentSearchResultEntity:
    require_permission(db, org_id, payload.user_id, "read_documents")
    hits = query_documents(f"org-{org_id}-documents", payload.query, size=payload.size)
    return DocumentSearchResultEntity(hits=hits)


def get_document_pipeline(document_id: str, acting_user_id: str, db: Session) -> DocumentPipelineEntity:
    document = db.get(db_entities.Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.DOCUMENT_NOT_FOUND)
    require_permission(db, document.organization_id, acting_user_id, "read_documents")
    events = (
        db.query(db_entities.PipelineEvent)
        .filter(db_entities.PipelineEvent.document_id == document_id)
        .order_by(db_entities.PipelineEvent.created_at.asc())
        .all()
    )
    return DocumentPipelineEntity(document=document, events=events)


def update_document_status(
    document_id: str,
    payload: models.DocumentStatusPatch,
    acting_user_id: str,
    db: Session,
) -> db_entities.Document:
    document = db.get(db_entities.Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.DOCUMENT_NOT_FOUND)
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
            db_entities.PipelineEvent(
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
    return document
