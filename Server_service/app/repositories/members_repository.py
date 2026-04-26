import json

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.entities import database as db_entities


def get_member(member_id: str, org_id: str, db: Session) -> db_entities.OrganizationMember | None:
    return (
        db.query(db_entities.OrganizationMember)
        .options(joinedload(db_entities.OrganizationMember.user))
        .filter(db_entities.OrganizationMember.id == member_id, db_entities.OrganizationMember.organization_id == org_id)
        .first()
    )


def get_membership(org_id: str, user_id: str, db: Session) -> db_entities.OrganizationMember | None:
    return (
        db.query(db_entities.OrganizationMember)
        .filter(
            db_entities.OrganizationMember.organization_id == org_id,
            db_entities.OrganizationMember.user_id == user_id,
        )
        .first()
    )


def create_member(
    *,
    org_id: str,
    user_id: str,
    role: str,
    permissions: list[str],
    status_value: str,
    db: Session,
) -> db_entities.OrganizationMember:
    member = db_entities.OrganizationMember(
        user_id=user_id,
        organization_id=org_id,
        role=role,
        permissions=json.dumps(permissions),
        status=status_value,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return (
        db.query(db_entities.OrganizationMember)
        .options(joinedload(db_entities.OrganizationMember.user))
        .filter(db_entities.OrganizationMember.id == member.id)
        .first()
    )


def list_members(
    org_id: str,
    search: str | None,
    skip: int,
    limit: int,
    db: Session,
) -> list[db_entities.OrganizationMember]:
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


def save_member(db: Session) -> None:
    db.commit()


def refresh_member(member: db_entities.OrganizationMember, db: Session) -> db_entities.OrganizationMember:
    db.refresh(member)
    return member


def count_active_admins(org_id: str, db: Session) -> int:
    return (
        db.query(db_entities.OrganizationMember)
        .filter(
            db_entities.OrganizationMember.organization_id == org_id,
            db_entities.OrganizationMember.role == "admin",
            db_entities.OrganizationMember.status == "active",
        )
        .count()
    )


def delete_member(member: db_entities.OrganizationMember, db: Session) -> None:
    db.delete(member)
    db.commit()
