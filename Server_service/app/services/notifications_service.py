from sqlalchemy.orm import Session

from app import models
from app.entities import database as db_entities
from app.repositories import notifications_repository


class NotificationsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_notification(self, payload: models.NotificationCreate) -> db_entities.Notification:
        return notifications_repository.create_notification(payload, self.db)

    def list_notifications(self, user_id: str, unread_only: bool) -> list[db_entities.Notification]:
        return notifications_repository.list_notifications(user_id, unread_only, self.db)

    def mark_notification_read(self, notification_id: str) -> db_entities.Notification:
        return notifications_repository.mark_notification_read(notification_id, self.db)
