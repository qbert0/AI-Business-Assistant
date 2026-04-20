from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_settings
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.services.inference_service import InferenceService


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackRead, summary="Luu feedback cho mot inference")
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)) -> FeedbackRead:
    return InferenceService(db, get_settings()).create_feedback(payload)


@router.get("", response_model=list[FeedbackRead], summary="Lay danh sach feedback")
def list_feedback(
    organization_id: str | None = Query(None),
    conversation_id: str | None = Query(None),
    model_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[FeedbackRead]:
    return InferenceService(db, get_settings()).list_feedback(
        organization_id=organization_id,
        conversation_id=conversation_id,
        model_id=model_id,
        limit=limit,
    )
