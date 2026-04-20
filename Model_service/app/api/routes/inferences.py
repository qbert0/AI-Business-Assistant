from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_settings
from app.schemas.inference import InferenceCreate, InferenceListItem, InferenceResult
from app.services.inference_service import InferenceService


router = APIRouter(prefix="/inferences", tags=["Inferences"])


@router.post("", response_model=InferenceResult, summary="Thuc hien mot inference va luu metadata")
def create_inference(payload: InferenceCreate, db: Session = Depends(get_db)) -> InferenceResult:
    return InferenceService(db, get_settings()).create_inference(payload)


@router.get("", response_model=list[InferenceListItem], summary="Lay danh sach inference records")
def list_inferences(
    conversation_id: str | None = Query(None),
    organization_id: str | None = Query(None),
    user_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[InferenceListItem]:
    return InferenceService(db, get_settings()).list_inferences(
        conversation_id=conversation_id,
        organization_id=organization_id,
        user_id=user_id,
        limit=limit,
    )


@router.get("/{request_id}", response_model=InferenceListItem, summary="Lay chi tiet inference record")
def get_inference(request_id: str, db: Session = Depends(get_db)) -> InferenceListItem:
    return InferenceService(db, get_settings()).get_inference(request_id)
