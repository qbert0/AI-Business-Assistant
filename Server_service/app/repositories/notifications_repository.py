from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.entities import database as db_entities
from app.repositories.common import dump_schema, get_org_or_404, get_user_or_404


def create_notification(payload: models.NotificationCreate, db: Session) -> db_entities.Notification:
    get_user_or_404(db, payload.user_id)
    if payload.organization_id:
        get_org_or_404(db, payload.organization_id)
    notification = db_entities.Notification(**dump_schema(payload))
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_notifications(user_id: str, unread_only: bool, db: Session) -> list[db_entities.Notification]:
    get_user_or_404(db, user_id)
    query = db.query(db_entities.Notification).filter(db_entities.Notification.user_id == user_id)
    if unread_only:
        query = query.filter(db_entities.Notification.is_read.is_(False))
    return query.order_by(db_entities.Notification.created_at.desc()).all()


def mark_notification_read(notification_id: str, db: Session) -> db_entities.Notification:
    notification = db.get(db_entities.Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification khong ton tai.")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
