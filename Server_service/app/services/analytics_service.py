from sqlalchemy.orm import Session

from app import models
from app.entities.api import AnalyticsEntity
from app.repositories import analytics_repository


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_analytics(self, org_id: str, acting_user_id: str) -> AnalyticsEntity:
        return analytics_repository.get_analytics(org_id, acting_user_id, self.db)

    def update_restrictions(
        self,
        org_id: str,
        payload: models.RestrictionUpdate,
        acting_user_id: str,
    ) -> AnalyticsEntity:
        return analytics_repository.update_restrictions(org_id, payload, acting_user_id, self.db)
