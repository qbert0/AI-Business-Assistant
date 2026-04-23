import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import messages
from app import models
from app.entities.api import OrganizationSettingsEntity
from app.entities import database as db_entities
from app.repositories.common import dump_schema, get_membership, get_org_or_404, get_user_or_404, parse_json_dict, require_permission


def update_my_settings(payload: models.UserSettingsUpdate, current_user: db_entities.User, db: Session) -> db_entities.User:
    return _update_user_settings(current_user, payload, db)


def get_user_settings(user_id: str, db: Session) -> db_entities.User:
    return get_user_or_404(db, user_id)


def update_user_settings(user_id: str, payload: models.UserSettingsUpdate, db: Session) -> db_entities.User:
    user = get_user_or_404(db, user_id)
    return _update_user_settings(user, payload, db)


def _update_user_settings(user: db_entities.User, payload: models.UserSettingsUpdate, db: Session) -> db_entities.User:
    for field, value in dump_schema(payload, exclude_unset=True).items():
        if field == "default_organization_id" and value is not None:
            if not get_membership(db, value, user.id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.USER_SETTINGS_ORG_INVALID)
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def get_organization_settings(org_id: str, acting_user_id: str, db: Session) -> OrganizationSettingsEntity:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    return OrganizationSettingsEntity(organization=org, settings=parse_json_dict(org.settings_json))


def update_organization_settings(
    org_id: str,
    payload: models.OrganizationSettingsUpdate,
    acting_user_id: str,
    db: Session,
) -> OrganizationSettingsEntity:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    data = dump_schema(payload, exclude_unset=True)
    settings_patch = data.pop("settings", None)
    for field, value in data.items():
        setattr(org, field, value)
    if settings_patch is not None:
        current_settings = parse_json_dict(org.settings_json)
        current_settings.update(settings_patch)
        org.settings_json = json.dumps(current_settings)
    db.commit()
    db.refresh(org)
    return OrganizationSettingsEntity(organization=org, settings=parse_json_dict(org.settings_json))
