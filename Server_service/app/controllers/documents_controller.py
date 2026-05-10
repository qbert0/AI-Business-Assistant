from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app import models
from app.constants.documents import (
    DOCUMENT_STATUS_FAILED,
    DOCUMENT_STATUS_INDEXED,
    DOCUMENT_STATUS_INDEXING,
    DOCUMENT_STATUS_PROCESSING,
    DOCUMENT_STATUS_PROCESSED,
    DOCUMENT_STATUS_UPLOADED,
)
from app.database import get_db
from app.dtos import document_dto
from app.services import DocumentsService

router = APIRouter()


@router.post(
    "/organizations/{org_id}/documents",
    response_model=models.DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Dang ky tai lieu va bat dau pipeline ingest",
)
def create_document(org_id: str, payload: models.DocumentCreate, db: Session = Depends(get_db)) -> models.DocumentRead:
    document = DocumentsService(db).create_document(org_id, payload)
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
    document = DocumentsService(db).upload_document_file(org_id, acting_user_id, file)
    return document_dto.to_document_model(document)


@router.post(
    "/organizations/{org_id}/documents/presign-upload",
    response_model=models.DocumentPresignedUploadRead,
    tags=["Documents"],
    summary="Tao presigned upload URL thong qua MinIO + api-gateway /storage",
)
def create_presigned_upload(
    org_id: str,
    payload: models.DocumentPresignedUploadRequest,
    db: Session = Depends(get_db),
) -> models.DocumentPresignedUploadRead:
    return models.DocumentPresignedUploadRead.model_validate(
        DocumentsService(db).create_presigned_upload(
            org_id,
            acting_user_id=payload.acting_user_id,
            file_name=payload.file_name,
            content_type=payload.content_type,
            expires=payload.expires,
        )
    )


@router.post(
    "/organizations/{org_id}/documents/complete-upload",
    response_model=models.DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Ghi metadata tai lieu vao DB sau khi client upload bang presigned URL",
)
def complete_presigned_upload(
    org_id: str,
    payload: models.DocumentPresignedUploadCompleteRequest,
    db: Session = Depends(get_db),
) -> models.DocumentRead:
    document = DocumentsService(db).complete_presigned_upload(org_id, payload)
    return document_dto.to_document_model(document)


@router.get("/organizations/{org_id}/documents", response_model=list[models.DocumentRead], tags=["Documents"], summary="Lay danh sach tai lieu cua to chuc")
def list_documents(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents."),
    status_filter: str | None = Query(
        None,
        alias="status",
        description=(
            f"{DOCUMENT_STATUS_UPLOADED}/{DOCUMENT_STATUS_PROCESSING}/"
            f"{DOCUMENT_STATUS_PROCESSED}/{DOCUMENT_STATUS_INDEXING}/"
            f"{DOCUMENT_STATUS_INDEXED}/{DOCUMENT_STATUS_FAILED}"
        ),
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.DocumentRead]:
    return document_dto.to_document_models(
        DocumentsService(db).list_documents(
            org_id,
            acting_user_id=acting_user_id,
            status_filter=status_filter,
            skip=skip,
            limit=limit,
        )
    )


@router.get(
    "/organizations/{org_id}/public/documents",
    response_model=list[models.DocumentRead],
    tags=["Documents"],
    summary="Lay danh sach tai lieu public cua to chuc cho guest",
)
def list_public_documents(
    org_id: str,
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.DocumentRead]:
    return document_dto.to_document_models(
        DocumentsService(db).list_public_documents(
            org_id,
            status_filter=status_filter,
            skip=skip,
            limit=limit,
        )
    )


@router.post("/organizations/{org_id}/documents/search", response_model=list[models.DocumentSearchHit], tags=["Documents"], summary="Tim tai lieu trong Elasticsearch")
def search_documents(
    org_id: str,
    payload: models.DocumentSearchRequest,
    db: Session = Depends(get_db),
) -> list[models.DocumentSearchHit]:
    entity = DocumentsService(db).search_documents(org_id, payload)
    return document_dto.to_document_search_hit_models(entity)


@router.get("/documents/{document_id}/pipeline", response_model=models.DocumentPipeline, tags=["Documents"], summary="Xem trang thai pipeline cua tai lieu")
def get_document_pipeline(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    db: Session = Depends(get_db),
) -> models.DocumentPipeline:
    entity = DocumentsService(db).get_document_pipeline(document_id, acting_user_id)
    return document_dto.to_document_pipeline_model(entity)


@router.post("/documents/{document_id}/analysis/start", response_model=models.DocumentRead, tags=["Documents"], summary="Bat dau phan tich tai lieu bang worker/rag pipeline")
def start_document_analysis(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen upload_documents."),
    db: Session = Depends(get_db),
) -> models.DocumentRead:
    document = DocumentsService(db).start_document_analysis(document_id, acting_user_id)
    return document_dto.to_document_model(document)


@router.post("/documents/{document_id}/analysis/stop", response_model=models.DocumentRead, tags=["Documents"], summary="Yeu cau dung pipeline phan tich tai lieu")
def stop_document_analysis(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen upload_documents."),
    db: Session = Depends(get_db),
) -> models.DocumentRead:
    document = DocumentsService(db).stop_document_analysis(document_id, acting_user_id)
    return document_dto.to_document_model(document)


@router.patch("/documents/{document_id}/status", response_model=models.DocumentRead, tags=["Documents"], summary="Cap nhat pipeline/status tai lieu")
def update_document_status(
    document_id: str,
    payload: models.DocumentStatusPatch,
    acting_user_id: str = Query(..., description="Can quyen upload_documents."),
    db: Session = Depends(get_db),
) -> models.DocumentRead:
    document = DocumentsService(db).update_document_status(document_id, payload, acting_user_id)
    return document_dto.to_document_model(document)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Documents"], summary="Xoa tai lieu")
def delete_document(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen upload_documents."),
    db: Session = Depends(get_db),
) -> None:
    DocumentsService(db).delete_document(document_id, acting_user_id)


@router.get("/documents/{document_id}/content", tags=["Documents"], summary="Doc noi dung file goc cua tai lieu")
def get_document_content(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    db: Session = Depends(get_db),
):
    return DocumentsService(db).get_document_content(document_id, acting_user_id)


@router.get(
    "/documents/{document_id}/download-url",
    response_model=models.DocumentPresignedDownloadRead,
    tags=["Documents"],
    summary="Lay presigned URL tai file thong qua api-gateway /storage",
)
def get_document_download_url(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    expires: int = Query(3600, ge=60, le=86400),
    db: Session = Depends(get_db),
) -> models.DocumentPresignedDownloadRead:
    return models.DocumentPresignedDownloadRead.model_validate(
        DocumentsService(db).get_document_download_url(
            document_id,
            acting_user_id,
            expires=expires,
        )
    )


@router.get("/documents/{document_id}/preview", response_model=models.DocumentPreviewRead, tags=["Documents"], summary="Lay noi dung preview cua tai lieu")
def get_document_preview(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    db: Session = Depends(get_db),
) -> models.DocumentPreviewRead:
    entity = DocumentsService(db).get_document_preview(document_id, acting_user_id)
    return document_dto.to_document_preview_model(entity)


@router.get("/documents/{document_id}/public/preview", response_model=models.DocumentPreviewRead, tags=["Documents"], summary="Lay preview tai lieu public cho guest")
def get_public_document_preview(
    document_id: str,
    db: Session = Depends(get_db),
) -> models.DocumentPreviewRead:
    entity = DocumentsService(db).get_public_document_preview(document_id)
    return document_dto.to_document_preview_model(entity)
