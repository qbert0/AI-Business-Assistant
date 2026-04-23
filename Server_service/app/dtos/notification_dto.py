from app import models
from app.entities import database as db_entities


def to_notification_model(notification: db_entities.Notification) -> models.NotificationRead:
    return models.NotificationRead(
        id=notification.id,
        user_id=notification.user_id,
        organization_id=notification.organization_id,
        notification_type=notification.notification_type,
        title=notification.title,
        content=notification.content,
        action_url=notification.action_url,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


def to_notification_models(notifications: list[db_entities.Notification]) -> list[models.NotificationRead]:
    return [to_notification_model(notification) for notification in notifications]
