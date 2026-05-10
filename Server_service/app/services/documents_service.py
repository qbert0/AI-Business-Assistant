import json
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import messages, models
from app.config import MINIO_BUCKET, SERVER_INTERNAL_URL
from app.constants.documents import (
    DOCUMENT_STATUS_INDEXED,
    DOCUMENT_STATUS_INDEXING,
    DOCUMENT_STATUS_PROCESSING,
    DOCUMENT_STATUS_CANCELLED,
    DOCUMENT_STATUS_UPLOADED,
    PIPELINE_STAGE_CHUNKING,
    PIPELINE_STAGE_GRAPH,
    PIPELINE_STAGE_INDEXING,
    PIPELINE_STAGE_INGEST,
    PIPELINE_STAGE_PARSING,
    PIPELINE_STAGE_UPLOAD,
)
from app.entities import database as db_entities
from app.entities.document import DocumentPipelineEntity, DocumentPreviewEntity, DocumentSearchResultEntity
from app.repositories import documents_repository
from app.repositories.common import parse_json_dict, parse_json_list
from app.services.document_preview import build_preview_payload, extract_document_text
from app.services.search_service import index_document, query_documents
from app.services.storage import (
    build_object_key,
    get_file_from_minio,
    get_object_metadata,
    get_presigned_upload_url,
    get_presigned_url,
    upload_file_to_minio,
)
from app.services.worker_queue import publish_document_analysis_job


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

    @staticmethod
    def _analysis_metadata_patch(
        *,
        state: str,
        locked: bool,
        parse_progress: int | None = None,
        graph_progress: int | None = None,
        stage: str | None = None,
        message: str | None = None,
        cancel_requested: bool | None = None,
        run_id: str | None = None,
        worker_message_id: str | None = None,
        error: str | None = None,
    ) -> dict:
        progress: dict[str, int] = {}
        if parse_progress is not None:
            progress["parse"] = max(0, min(100, parse_progress))
        if graph_progress is not None:
            progress["graph"] = max(0, min(100, graph_progress))

        analysis: dict[str, object] = {"state": state, "locked": locked}
        if progress:
            analysis["progress"] = progress
        if stage is not None:
            analysis["stage"] = stage
        if message is not None:
            analysis["message"] = message
        if cancel_requested is not None:
            analysis["cancel_requested"] = cancel_requested
        if run_id is not None:
            analysis["run_id"] = run_id
        if worker_message_id is not None:
            analysis["worker_message_id"] = worker_message_id
        if error is not None:
            analysis["error"] = error
        return {"analysis": analysis}

    def _mark_document_indexed(
        self,
        document: db_entities.Document,
        *,
        actor_user_id: str,
        content_text: str | None,
    ) -> None:
        document.status = DOCUMENT_STATUS_INDEXING
        document.chunk_count = "1"
        index_document(document, content_text=content_text)
        documents_repository.create_pipeline_event(
            organization_id=document.organization_id,
            document_id=document.id,
            actor_user_id=actor_user_id,
            stage=PIPELINE_STAGE_INDEXING,
            status=DOCUMENT_STATUS_INDEXING,
            message=messages.DOCUMENT_RAG_INDEXING,
            db=self.db,
        )
        document.status = DOCUMENT_STATUS_INDEXED
        documents_repository.create_pipeline_event(
            organization_id=document.organization_id,
            document_id=document.id,
            actor_user_id=actor_user_id,
            stage=PIPELINE_STAGE_INDEXING,
            status=DOCUMENT_STATUS_INDEXED,
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
        document.status = DOCUMENT_STATUS_UPLOADED
        documents_repository.create_pipeline_event(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=payload.uploaded_by_user_id,
            stage=PIPELINE_STAGE_INGEST,
            status=DOCUMENT_STATUS_UPLOADED,
            message=messages.DOCUMENT_INGEST_ACCEPTED,
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
        document.status = DOCUMENT_STATUS_UPLOADED
        documents_repository.create_pipeline_event(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage=PIPELINE_STAGE_UPLOAD,
            status=DOCUMENT_STATUS_UPLOADED,
            message=messages.DOCUMENT_UPLOADED,
            db=self.db,
        )
        document.status = DOCUMENT_STATUS_PROCESSING
        documents_repository.create_pipeline_event(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage=PIPELINE_STAGE_PARSING,
            status=DOCUMENT_STATUS_PROCESSING,
            message=messages.DOCUMENT_PARSED,
            db=self.db,
        )
        documents_repository.create_pipeline_event(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage=PIPELINE_STAGE_CHUNKING,
            status=DOCUMENT_STATUS_PROCESSING,
            message=messages.DOCUMENT_CHUNKED,
            db=self.db,
        )
        self._mark_document_indexed(document, actor_user_id=acting_user_id, content_text=extracted_text)
        documents_repository.save_document(self.db)
        return documents_repository.refresh_document(document, self.db)

    def create_presigned_upload(
        self,
        org_id: str,
        *,
        acting_user_id: str,
        file_name: str,
        content_type: str | None,
        expires: int,
    ) -> dict[str, str | int | None]:
        self._ensure_org_exists(org_id)
        if not documents_repository.get_user(acting_user_id, self.db):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
        self._require_permission(org_id, acting_user_id, "upload_documents")

        object_key = build_object_key(org_id, file_name)
        upload_url = get_presigned_upload_url(
            MINIO_BUCKET,
            object_key,
            expires,
            content_type=content_type,
        )
        return {
            "bucket": MINIO_BUCKET,
            "object_key": object_key,
            "upload_url": upload_url,
            "source_url": f"s3://{MINIO_BUCKET}/{object_key}",
            "expires_in": expires,
            "content_type": content_type,
        }

    def complete_presigned_upload(
        self,
        org_id: str,
        payload: models.DocumentPresignedUploadCompleteRequest,
    ) -> db_entities.Document:
        self._ensure_org_exists(org_id)
        uploader = documents_repository.get_user(payload.acting_user_id, self.db)
        if not uploader:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
        self._require_permission(org_id, payload.acting_user_id, "upload_documents")

        object_metadata = get_object_metadata(payload.bucket, payload.object_key)
        source_url = f"s3://{payload.bucket}/{payload.object_key}"
        metadata = {
            **payload.metadata,
            "uploaded_by_email": uploader.email,
            "content_type": payload.content_type or object_metadata.content_type,
            "storage_provider": "minio",
            "bucket": payload.bucket,
            "object_key": payload.object_key,
            "size_bytes": object_metadata.size,
            "etag": object_metadata.etag,
            "last_modified": object_metadata.last_modified.isoformat() if object_metadata.last_modified else None,
        }
        document = documents_repository.create_document(
            org_id=org_id,
            uploaded_by_user_id=payload.acting_user_id,
            file_name=payload.file_name,
            source_url=source_url,
            metadata_json=json.dumps(metadata),
            vector_index=f"org-{org_id}-documents",
            db=self.db,
        )
        document.status = DOCUMENT_STATUS_UPLOADED
        documents_repository.create_pipeline_event(
            organization_id=org_id,
            document_id=document.id,
            actor_user_id=payload.acting_user_id,
            stage=PIPELINE_STAGE_UPLOAD,
            status=DOCUMENT_STATUS_UPLOADED,
            message=messages.DOCUMENT_REGISTERED,
            db=self.db,
        )
        documents_repository.save_document(self.db)
        return documents_repository.refresh_document(document, self.db)

    def start_document_analysis(self, document_id: str, acting_user_id: str) -> db_entities.Document:
        document = self._get_document_or_404(document_id)
        self._require_permission(document.organization_id, acting_user_id, "upload_documents")
        if document.status in {DOCUMENT_STATUS_PROCESSING, DOCUMENT_STATUS_INDEXING}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tai lieu dang duoc xu ly.")

        metadata = parse_json_dict(document.metadata_json)
        bucket = metadata.get("bucket")
        object_key = metadata.get("object_key")
        if not bucket or not object_key:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.DOCUMENT_STORAGE_METADATA_INVALID)

        run_id = str(uuid4())
        document.status = DOCUMENT_STATUS_PROCESSING
        documents_repository.merge_document_metadata(
            document,
            self._analysis_metadata_patch(
                state="queued",
                locked=True,
                parse_progress=0,
                graph_progress=0,
                stage=PIPELINE_STAGE_INGEST,
                message=messages.DOCUMENT_ANALYSIS_QUEUED,
                cancel_requested=False,
                run_id=run_id,
                error=None,
            ),
        )
        documents_repository.create_pipeline_event(
            organization_id=document.organization_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage=PIPELINE_STAGE_INGEST,
            status=DOCUMENT_STATUS_PROCESSING,
            message=messages.DOCUMENT_ANALYSIS_QUEUED,
            db=self.db,
        )

        worker_message_id = publish_document_analysis_job(
            {
                "document_id": document.id,
                "organization_id": document.organization_id,
                "acting_user_id": acting_user_id,
                "run_id": run_id,
                "file_name": document.file_name,
                "source_url": document.source_url,
                "bucket": bucket,
                "object_key": object_key,
                "content_url": f"{SERVER_INTERNAL_URL}/documents/{document.id}/content?acting_user_id={acting_user_id}",
            }
        )
        documents_repository.merge_document_metadata(
            document,
            self._analysis_metadata_patch(
                state="queued",
                locked=True,
                worker_message_id=worker_message_id,
            ),
        )
        documents_repository.save_document(self.db)
        return documents_repository.refresh_document(document, self.db)

    def stop_document_analysis(self, document_id: str, acting_user_id: str) -> db_entities.Document:
        document = self._get_document_or_404(document_id)
        self._require_permission(document.organization_id, acting_user_id, "upload_documents")
        if document.status not in {DOCUMENT_STATUS_PROCESSING, DOCUMENT_STATUS_INDEXING}:
            return document

        documents_repository.merge_document_metadata(
            document,
            self._analysis_metadata_patch(
                state="stopping",
                locked=True,
                stage="stopping",
                message=messages.DOCUMENT_ANALYSIS_STOP_REQUESTED,
                cancel_requested=True,
            ),
        )
        documents_repository.create_pipeline_event(
            organization_id=document.organization_id,
            document_id=document.id,
            actor_user_id=acting_user_id,
            stage="stopping",
            status=document.status,
            message=messages.DOCUMENT_ANALYSIS_STOP_REQUESTED,
            db=self.db,
        )
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
        metadata_patch: dict = {}
        if payload.metadata:
            metadata_patch.update(payload.metadata)
        if payload.analysis:
            metadata_patch.setdefault("analysis", {}).update(payload.analysis)
        if payload.progress:
            metadata_patch.setdefault("analysis", {}).setdefault("progress", {}).update(payload.progress)
        if metadata_patch:
            documents_repository.merge_document_metadata(document, metadata_patch)
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

    def get_document_download_url(
        self,
        document_id: str,
        acting_user_id: str,
        *,
        expires: int,
    ) -> dict[str, str | int]:
        document = self._get_document_or_404(document_id)
        self._require_permission(document.organization_id, acting_user_id, "read_documents")
        metadata = parse_json_dict(document.metadata_json)
        bucket = metadata.get("bucket")
        object_key = metadata.get("object_key")
        if not bucket or not object_key:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.DOCUMENT_STORAGE_METADATA_INVALID)
        return {
            "document_id": document.id,
            "file_name": document.file_name,
            "download_url": get_presigned_url(bucket, object_key, expires),
            "expires_in": expires,
        }

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
