from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.dtos import common_dto, settings_dto
from app.entities import database as db_entities
from app.repositories import settings_repository
from app.services.security import get_current_user

router = APIRouter()


@router.get("/settings/profile", response_model=models.UserRead, tags=["Settings"], summary="Lay cai dat ca nhan bang JWT")
def get_my_settings(current_user: db_entities.User = Depends(get_current_user)) -> models.UserRead:
    return common_dto.to_user_model(current_user)


@router.patch("/settings/profile", response_model=models.UserRead, tags=["Settings"], summary="Cap nhat cai dat ca nhan bang JWT")
def update_my_settings(
    payload: models.UserSettingsUpdate,
    current_user: db_entities.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.UserRead:
    user = settings_repository.update_my_settings(payload, current_user, db)
    return common_dto.to_user_model(user)


@router.get("/users/{user_id}/settings", response_model=models.UserRead, tags=["Settings"], summary="Lay cai dat ca nhan theo user_id")
def get_user_settings(user_id: str, db: Session = Depends(get_db)) -> models.UserRead:
    user = settings_repository.get_user_settings(user_id, db)
    return common_dto.to_user_model(user)


@router.patch("/users/{user_id}/settings", response_model=models.UserRead, tags=["Settings"], summary="Cap nhat cai dat ca nhan theo user_id")
def update_user_settings(user_id: str, payload: models.UserSettingsUpdate, db: Session = Depends(get_db)) -> models.UserRead:
    user = settings_repository.update_user_settings(user_id, payload, db)
    return common_dto.to_user_model(user)


@router.get("/organizations/{org_id}/settings", response_model=models.OrganizationSettingsRead, tags=["Settings"], summary="Lay cai dat to chuc")
def get_organization_settings(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.OrganizationSettingsRead:
    settings = settings_repository.get_organization_settings(org_id, acting_user_id, db)
    return settings_dto.to_organization_settings_model(settings)


@router.patch("/organizations/{org_id}/settings", response_model=models.OrganizationSettingsRead, tags=["Settings"], summary="Cap nhat cai dat to chuc")
def update_organization_settings(
    org_id: str,
    payload: models.OrganizationSettingsUpdate,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.OrganizationSettingsRead:
    settings = settings_repository.update_organization_settings(org_id, payload, acting_user_id, db)
    return settings_dto.to_organization_settings_model(settings)
