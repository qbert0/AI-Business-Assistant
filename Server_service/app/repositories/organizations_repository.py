import json

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.constants.permissions import ADMIN_PERMISSIONS
from app import models
from app.entities import database as db_entities
from app.entities.api import OrganizationDashboardEntity
from app.repositories.common import dump_schema, get_membership, get_org_or_404, get_user_or_404, require_permission


def create_organization(payload: models.OrganizationCreate, db: Session) -> db_entities.Organization:
    get_user_or_404(db, payload.owner_user_id)
    org = db_entities.Organization(name=payload.name, industry=payload.industry, description=payload.description)
    db.add(org)
    db.flush()
    member = db_entities.OrganizationMember(
        user_id=payload.owner_user_id,
        organization_id=org.id,
        role="admin",
        permissions=json.dumps(ADMIN_PERMISSIONS),
        status="active",
    )
    db.add(member)
    db.commit()
    db.refresh(org)
    return org


def list_organizations(
    search: str | None,
    user_id: str | None,
    skip: int,
    limit: int,
    db: Session,
) -> list[db_entities.Organization]:
    query = db.query(db_entities.Organization)
    if user_id:
        query = query.join(db_entities.OrganizationMember).filter(db_entities.OrganizationMember.user_id == user_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                db_entities.Organization.name.like(like),
                db_entities.Organization.industry.like(like),
                db_entities.Organization.description.like(like),
            )
        )
    return query.order_by(db_entities.Organization.created_at.desc()).offset(skip).limit(limit).all()


def get_organization(org_id: str, db: Session) -> db_entities.Organization:
    return get_org_or_404(db, org_id)


def update_organization(
    org_id: str,
    payload: models.OrganizationUpdate,
    acting_user_id: str,
    db: Session,
) -> db_entities.Organization:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    for field, value in dump_schema(payload, exclude_unset=True).items():
        setattr(org, field, value)
    db.commit()
    db.refresh(org)
    return org


def organization_dashboard(org_id: str, acting_user_id: str, db: Session) -> OrganizationDashboardEntity:
    org = get_org_or_404(db, org_id)
    if not get_membership(db, org_id, acting_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User khong thuoc to chuc nay.")
    document_count = db.query(db_entities.Document).filter(db_entities.Document.organization_id == org_id).count()
    return OrganizationDashboardEntity(
        organization=org,
        employee_count=db.query(db_entities.OrganizationMember).filter(db_entities.OrganizationMember.organization_id == org_id).count(),
        document_count=document_count,
        indexed_document_count=db.query(db_entities.Document)
        .filter(db_entities.Document.organization_id == org_id, db_entities.Document.status == "completed")
        .count(),
        chat_session_count=db.query(db_entities.ChatSession).filter(db_entities.ChatSession.organization_id == org_id).count(),
        suggested_questions=[
            "Chinh sach nghi phep cua cong ty la gi?",
            "Quy trinh phe duyet chi phi noi bo nhu the nao?",
            "Nhan vien moi can doc tai lieu nao dau tien?",
        ],
    )
