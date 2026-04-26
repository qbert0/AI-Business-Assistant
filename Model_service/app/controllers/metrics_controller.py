from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_db
from app.repositories import MetricsRepository


router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary", response_model=models.MetricSummaryResponse, summary="Lay metric tong hop theo model")
def get_metric_summary(
    hours: int = Query(24, ge=1, le=720),
    model_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> models.MetricSummaryResponse:
    return MetricsRepository(db).summarize(hours=hours, model_id=model_id)

