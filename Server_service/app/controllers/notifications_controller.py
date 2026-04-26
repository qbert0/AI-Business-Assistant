from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.dtos import notification_dto
from app.entities import database as db_entities
from app.repositories import notifications_repository

router = APIRouter()


@router.post("/notifications", response_model=models.NotificationRead, status_code=status.HTTP_201_CREATED, tags=["Notifications"], summary="Tao notification")
def create_notification(payload: models.NotificationCreate, db: Session = Depends(get_db)) -> models.NotificationRead:
    notification = notifications_repository.create_notification(payload, db)
    return notification_dto.to_notification_model(notification)


@router.get("/users/{user_id}/notifications", response_model=list[models.NotificationRead], tags=["Notifications"], summary="Lay notification cua user")
def list_notifications(user_id: str, unread_only: bool = False, db: Session = Depends(get_db)) -> list[models.NotificationRead]:
    notifications = notifications_repository.list_notifications(user_id, unread_only, db)
    return notification_dto.to_notification_models(notifications)


@router.patch("/notifications/{notification_id}/read", response_model=models.NotificationRead, tags=["Notifications"], summary="Danh dau notification da doc")
def mark_notification_read(notification_id: str, db: Session = Depends(get_db)) -> models.NotificationRead:
    notification = notifications_repository.mark_notification_read(notification_id, db)
    return notification_dto.to_notification_model(notification)
