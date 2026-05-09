from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_db, get_settings
from app.services.inference_service import InferenceService


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=models.FeedbackRead, summary="Luu feedback cho mot inference")
def create_feedback(payload: models.FeedbackCreate, db: Session = Depends(get_db)) -> models.FeedbackRead:
    return InferenceService.from_dependencies(db, get_settings()).create_feedback(payload)


@router.get("", response_model=list[models.FeedbackRead], summary="Lay danh sach feedback")
def list_feedback(
    organization_id: str | None = Query(None),
    conversation_id: str | None = Query(None),
    model_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[models.FeedbackRead]:
    return InferenceService.from_dependencies(db, get_settings()).list_feedback(
        organization_id=organization_id,
        conversation_id=conversation_id,
        model_id=model_id,
        limit=limit,
    )
