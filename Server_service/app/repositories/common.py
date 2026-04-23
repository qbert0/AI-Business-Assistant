import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import messages
from app.entities import database as db_entities


def parse_json_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def parse_json_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def dump_schema(schema, **kwargs) -> dict:
    if hasattr(schema, "model_dump"):
        return schema.model_dump(**kwargs)
    return schema.dict(**kwargs)


def get_user_or_404(db: Session, user_id: str) -> db_entities.User:
    user = db.get(db_entities.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
    return user


def get_org_or_404(db: Session, org_id: str) -> db_entities.Organization:
    org = db.get(db_entities.Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)
    return org


def get_membership(db: Session, org_id: str, user_id: str) -> db_entities.OrganizationMember | None:
    return (
        db.query(db_entities.OrganizationMember)
        .filter(
            db_entities.OrganizationMember.organization_id == org_id,
            db_entities.OrganizationMember.user_id == user_id,
            db_entities.OrganizationMember.status == "active",
        )
        .first()
    )


def require_permission(db: Session, org_id: str, user_id: str, permission: str) -> db_entities.OrganizationMember:
    membership = get_membership(db, org_id, user_id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
    permissions = parse_json_list(membership.permissions)
    if membership.role != "admin" and permission not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
    return membership
