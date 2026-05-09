from sqlalchemy.orm import Session

from app import models
from app.entities import database as db_entities
from app.entities.api import OrganizationSettingsEntity
from app.repositories import settings_repository


class SettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_my_settings(self, payload: models.UserSettingsUpdate, current_user: db_entities.User) -> db_entities.User:
        return settings_repository.update_my_settings(payload, current_user, self.db)

    def get_user_settings(self, user_id: str) -> db_entities.User:
        return settings_repository.get_user_settings(user_id, self.db)

    def update_user_settings(self, user_id: str, payload: models.UserSettingsUpdate) -> db_entities.User:
        return settings_repository.update_user_settings(user_id, payload, self.db)

    def get_organization_settings(self, org_id: str, acting_user_id: str) -> OrganizationSettingsEntity:
        return settings_repository.get_organization_settings(org_id, acting_user_id, self.db)

    def update_organization_settings(
        self,
        org_id: str,
        payload: models.OrganizationSettingsUpdate,
        acting_user_id: str,
    ) -> OrganizationSettingsEntity:
        return settings_repository.update_organization_settings(org_id, payload, acting_user_id, self.db)
