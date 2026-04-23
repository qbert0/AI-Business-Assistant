import json

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app import messages
from app import models
from app.entities import database as db_entities
from app.repositories.common import get_membership, get_org_or_404, get_user_or_404, require_permission
from app.services.security import permissions_for_role


def add_member(org_id: str, payload: models.MemberCreate, acting_user_id: str, db: Session) -> db_entities.OrganizationMember:
    get_org_or_404(db, org_id)
    get_user_or_404(db, payload.user_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    if get_membership(db, org_id, payload.user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.MEMBER_ALREADY_EXISTS)
    member = db_entities.OrganizationMember(
        user_id=payload.user_id,
        organization_id=org_id,
        role=payload.role,
        permissions=json.dumps(permissions_for_role(payload.role, payload.permissions)),
        status=payload.status,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    member = db.query(db_entities.OrganizationMember).options(joinedload(db_entities.OrganizationMember.user)).get(member.id)
    return member


def list_members(
    org_id: str,
    acting_user_id: str,
    search: str | None,
    skip: int,
    limit: int,
    db: Session,
) -> list[db_entities.OrganizationMember]:
    require_permission(db, org_id, acting_user_id, "view_employees")
    query = (
        db.query(db_entities.OrganizationMember)
        .options(joinedload(db_entities.OrganizationMember.user))
        .join(db_entities.User)
        .filter(db_entities.OrganizationMember.organization_id == org_id)
    )
    if search:
        like = f"%{search}%"
        query = query.filter(or_(db_entities.User.email.like(like), db_entities.User.full_name.like(like)))
    return query.order_by(db_entities.OrganizationMember.joined_at.desc()).offset(skip).limit(limit).all()


def update_member(
    org_id: str,
    member_id: str,
    payload: models.MemberPatch,
    acting_user_id: str,
    db: Session,
) -> db_entities.OrganizationMember:
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    member = (
        db.query(db_entities.OrganizationMember)
        .options(joinedload(db_entities.OrganizationMember.user))
        .filter(db_entities.OrganizationMember.id == member_id, db_entities.OrganizationMember.organization_id == org_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.MEMBER_NOT_FOUND)
    if payload.role is not None:
        member.role = payload.role
        if payload.permissions is None:
            member.permissions = json.dumps(permissions_for_role(payload.role))
    if payload.permissions is not None:
        member.permissions = json.dumps(permissions_for_role(payload.role or member.role, payload.permissions))
    if payload.status is not None:
        member.status = payload.status
    db.commit()
    db.refresh(member)
    return member


def delete_member(org_id: str, member_id: str, acting_user_id: str, db: Session) -> None:
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    member = (
        db.query(db_entities.OrganizationMember)
        .filter(db_entities.OrganizationMember.id == member_id, db_entities.OrganizationMember.organization_id == org_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.MEMBER_NOT_FOUND)
    db.delete(member)
    db.commit()


def leave_organization(org_id: str, acting_user_id: str, db: Session) -> None:
    member = (
        db.query(db_entities.OrganizationMember)
        .filter(
            db_entities.OrganizationMember.organization_id == org_id,
            db_entities.OrganizationMember.user_id == acting_user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_IN_ORGANIZATION)
    if member.role == "admin":
        active_admin_count = (
            db.query(db_entities.OrganizationMember)
            .filter(
                db_entities.OrganizationMember.organization_id == org_id,
                db_entities.OrganizationMember.role == "admin",
                db_entities.OrganizationMember.status == "active",
            )
            .count()
        )
        if active_admin_count <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.LAST_ADMIN_CANNOT_LEAVE)
    db.delete(member)
    db.commit()
