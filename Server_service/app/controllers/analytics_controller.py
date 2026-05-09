from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.dtos import analytics_dto
from app.services import AnalyticsService

router = APIRouter()


@router.get("/organizations/{org_id}/analytics", response_model=models.AnalyticsRead, tags=["Analytics"], summary="Lay analytics cua to chuc")
def get_analytics(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen view_analytics."),
    db: Session = Depends(get_db),
) -> models.AnalyticsRead:
    analytics = AnalyticsService(db).get_analytics(org_id, acting_user_id)
    return analytics_dto.to_analytics_model(analytics)


@router.put("/organizations/{org_id}/analytics/restrictions", response_model=models.AnalyticsRead, tags=["Analytics"], summary="Cap nhat han che noi dung nhay cam")
def update_restrictions(
    org_id: str,
    payload: models.RestrictionUpdate,
    acting_user_id: str = Query(..., description="Can quyen edit_sensitive_restrictions."),
    db: Session = Depends(get_db),
) -> models.AnalyticsRead:
    analytics = AnalyticsService(db).update_restrictions(org_id, payload, acting_user_id)
    return analytics_dto.to_analytics_model(analytics)
