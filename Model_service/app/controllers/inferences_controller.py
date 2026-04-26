from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_db, get_settings
from app.repositories import InferenceRepository


router = APIRouter(prefix="/inferences", tags=["Inferences"])


@router.post("", response_model=models.InferenceResult, summary="Thuc hien mot inference va luu metadata")
def create_inference(payload: models.InferenceCreate, db: Session = Depends(get_db)) -> models.InferenceResult:
    return InferenceRepository(db, get_settings()).create_inference(payload)


@router.get("", response_model=list[models.InferenceListItem], summary="Lay danh sach inference records")
def list_inferences(
    conversation_id: str | None = Query(None),
    organization_id: str | None = Query(None),
    user_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.InferenceListItem]:
    return InferenceRepository(db, get_settings()).list_inferences(
        conversation_id=conversation_id,
        organization_id=organization_id,
        user_id=user_id,
        limit=limit,
    )


@router.get("/{request_id}", response_model=models.InferenceListItem, summary="Lay chi tiet inference record")
def get_inference(request_id: str, db: Session = Depends(get_db)) -> models.InferenceListItem:
    return InferenceRepository(db, get_settings()).get_inference(request_id)

