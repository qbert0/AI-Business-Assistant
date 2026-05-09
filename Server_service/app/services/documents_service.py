import json

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import messages, models
from app.entities import database as db_entities
from app.entities.document import DocumentPipelineEntity, DocumentPreviewEntity, DocumentSearchResultEntity
from app.repositories import documents_repository
from app.repositories.common import parse_json_dict, parse_json_list
from app.services.document_preview import build_preview_payload, extract_document_text
from app.services.search_service import index_document, query_documents
from app.services.storage import get_file_from_minio, upload_file_to_minio


class DocumentsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_membership(self, org_id: str, user_id: str) -> db_entities.OrganizationMember | None:
        return (
            self.db.query(db_entities.OrganizationMember)
            .filter(
                db_entities.OrganizationMember.organization_id == org_id,
                db_entities.OrganizationMember.user_id == user_id,
                db_entities.OrganizationMember.status == "active",
            )
            .first()
        )

    def _require_permission(self, org_id: str, user_id: str, permission: str) -> db_entities.OrganizationMember:
        membership = self._get_membership(org_id, user_id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
        permissions = parse_json_list(membership.permissions)
        if membership.role != "admin" and permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
        return membership

    def _get_document_or_404(self, document_id: str) -> db_entities.Document:
        document = documents_repository.get_document(document_id, self.db)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.DOCUMENT_NOT_FOUND)
        return document

    def _ensure_org_exists(self, org_id: str) -> None:
        if not documents_repository.get_organization(org_id, self.db):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)

    def _mark_document_indexed(
        self,
        document: db_entities.Document,
        *,
        actor_user_id: str,
        content_text: str | None,
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
            db=self.db,
        )

    def create_document(self, org_id: str, payload: models.DocumentCreate) -> db_entities.Document:
        self._ensure_org_exists(org_id)
        self._require_permission(org_id, payload.uploaded_by_user_id, "upload_documents")
        document = documents_repository.create_document(
            org_id=org_id,
            uploaded_by_user_id=payload.uploaded_by_user_id,
            file_name=payload.file_name,
            source_url=payload.source_url,
            metadata_json=json.dumps(payload.metadata),
            vector_index=f"org-{org_id}-documents",
            db=self.db,
        )
        documents_repository.create_pipeline_event(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=payload.uploaded_by_user_id,
            stage="ingest",
            status="processing",
            message="Tai lieu da duoc ghi nhan, dang index vao Search-service.",
            db=self.db,
        )
        self._mark_document_indexed(document, actor_user_id=payload.uploaded_by_user_id, content_text=None)
        documents_repository.save_document(self.db)
        return documents_repository.refresh_document(document, self.db)

    def upload_document_file(self, org_id: str, acting_user_id: str, file: UploadFile) -> db_entities.Document:
        self._ensure_org_exists(org_id)
        uploader = documents_repository.get_user(acting_user_id, self.db)
        if not uploader:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
        self._require_permission(org_id, acting_user_id, "upload_documents")

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
            db=self.db,
        )
        documents_repository.create_pipeline_event(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage="upload",
            status="processing",
            message="File da duoc luu trong MinIO va metadata da duoc ghi vao database.",
            db=self.db,
        )
        self._mark_document_indexed(document, actor_user_id=acting_user_id, content_text=extracted_text)
        documents_repository.save_document(self.db)
        return documents_repository.refresh_document(document, self.db)

    def list_documents(
        self,
        org_id: str,
        *,
        acting_user_id: str,
        status_filter: str | None,
        skip: int,
        limit: int,
    ) -> list[db_entities.Document]:
        self._require_permission(org_id, acting_user_id, "read_documents")
        return documents_repository.list_documents(org_id, status_filter, skip, limit, self.db)

    def search_documents(self, org_id: str, payload: models.DocumentSearchRequest) -> DocumentSearchResultEntity:
        self._require_permission(org_id, payload.user_id, "read_documents")
        try:
            hits = query_documents(f"org-{org_id}-documents", payload.query, size=payload.size)
        except HTTPException:
            hits = []
        return DocumentSearchResultEntity(hits=hits)

    def get_document_pipeline(self, document_id: str, acting_user_id: str) -> DocumentPipelineEntity:
        document = self._get_document_or_404(document_id)
        self._require_permission(document.organization_id, acting_user_id, "read_documents")
        return DocumentPipelineEntity(
            document=document,
            events=documents_repository.list_pipeline_events(document_id, self.db),
        )

    def update_document_status(
        self,
        document_id: str,
        payload: models.DocumentStatusPatch,
        acting_user_id: str,
    ) -> db_entities.Document:
        document = self._get_document_or_404(document_id)
        self._require_permission(document.organization_id, acting_user_id, "upload_documents")
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
                db=self.db,
            )
        documents_repository.save_document(self.db)
        return documents_repository.refresh_document(document, self.db)

    def get_document_content(self, document_id: str, acting_user_id: str) -> StreamingResponse:
        document = self._get_document_or_404(document_id)
        self._require_permission(document.organization_id, acting_user_id, "read_documents")
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

    def get_document_preview(self, document_id: str, acting_user_id: str) -> DocumentPreviewEntity:
        document = self._get_document_or_404(document_id)
        self._require_permission(document.organization_id, acting_user_id, "read_documents")
        metadata = parse_json_dict(document.metadata_json)
        bucket = metadata.get("bucket")
        object_key = metadata.get("object_key")
        if not bucket or not object_key:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.DOCUMENT_STORAGE_METADATA_INVALID)
        minio_response = get_file_from_minio(bucket, object_key)
        file_bytes = minio_response["Body"].read()
        preview = build_preview_payload(document.file_name, file_bytes)
        return DocumentPreviewEntity(document=document, kind=preview.kind, content=preview.content, message=preview.message)
