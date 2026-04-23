from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.dtos import document_dto
from app.repositories import documents_repository

router = APIRouter()


@router.post(
    "/organizations/{org_id}/documents",
    response_model=models.DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Documents"],
    summary="Dang ky tai lieu va bat dau pipeline ingest",
)
def create_document(org_id: str, payload: models.DocumentCreate, db: Session = Depends(get_db)) -> models.DocumentRead:
    document = documents_repository.create_document(org_id, payload, db)
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
    document = documents_repository.upload_document_file(org_id, acting_user_id, file, db)
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
    documents = documents_repository.list_documents(org_id, acting_user_id, status_filter, skip, limit, db)
    return document_dto.to_document_models(documents)


@router.post("/organizations/{org_id}/documents/search", response_model=list[models.DocumentSearchHit], tags=["Documents"], summary="Tim tai lieu trong Elasticsearch")
def search_documents(
    org_id: str,
    payload: models.DocumentSearchRequest,
    db: Session = Depends(get_db),
) -> list[models.DocumentSearchHit]:
    result = documents_repository.search_documents(org_id, payload, db)
    return document_dto.to_document_search_hit_models(result)


@router.get("/documents/{document_id}/pipeline", response_model=models.DocumentPipeline, tags=["Documents"], summary="Xem trang thai pipeline cua tai lieu")
def get_document_pipeline(
    document_id: str,
    acting_user_id: str = Query(..., description="Can quyen read_documents trong to chuc cua tai lieu."),
    db: Session = Depends(get_db),
) -> models.DocumentPipeline:
    pipeline = documents_repository.get_document_pipeline(document_id, acting_user_id, db)
    return document_dto.to_document_pipeline_model(pipeline)


@router.patch("/documents/{document_id}/status", response_model=models.DocumentRead, tags=["Documents"], summary="Cap nhat pipeline/status tai lieu")
def update_document_status(
    document_id: str,
    payload: models.DocumentStatusPatch,
    acting_user_id: str = Query(..., description="Can quyen upload_documents."),
    db: Session = Depends(get_db),
) -> models.DocumentRead:
    document = documents_repository.update_document_status(document_id, payload, acting_user_id, db)
    return document_dto.to_document_model(document)
