import json

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.constants.documents import DOCUMENT_INDEXED_STATUSES
from app.constants.permissions import ADMIN_PERMISSIONS
from app.entities import database as db_entities
from app.entities.api import OrganizationDashboardEntity
from app.repositories.common import parse_json_dict


def create_organization(
    *,
    name: str,
    industry: str | None,
    description: str | None,
    owner_user_id: str,
    db: Session,
) -> db_entities.Organization:
    org = db_entities.Organization(name=name, industry=industry, description=description)
    db.add(org)
    db.flush()
    db.add(
        db_entities.OrganizationMember(
            user_id=owner_user_id,
            organization_id=org.id,
            role="admin",
            permissions=json.dumps(ADMIN_PERMISSIONS),
            status="active",
        )
    )
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
        query = query.join(db_entities.OrganizationMember).filter(
            db_entities.OrganizationMember.user_id == user_id,
            db_entities.OrganizationMember.status == "active",
        )
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                db_entities.Organization.name.like(like),
                db_entities.Organization.industry.like(like),
                db_entities.Organization.description.like(like),
                db_entities.Organization.settings_json.like(like),
            )
        )
    return query.order_by(db_entities.Organization.created_at.desc()).offset(skip).limit(limit).all()


def get_organization(org_id: str, db: Session) -> db_entities.Organization | None:
    return db.get(db_entities.Organization, org_id)


def get_membership(org_id: str, user_id: str, db: Session) -> db_entities.OrganizationMember | None:
    return (
        db.query(db_entities.OrganizationMember)
        .filter(
            db_entities.OrganizationMember.organization_id == org_id,
            db_entities.OrganizationMember.user_id == user_id,
            db_entities.OrganizationMember.status == "active",
        )
        .first()
    )


def save_organization(db: Session) -> None:
    db.commit()


def refresh_organization(org: db_entities.Organization, db: Session) -> db_entities.Organization:
    db.refresh(org)
    return org


def build_dashboard(org: db_entities.Organization, db: Session) -> OrganizationDashboardEntity:
    org_id = org.id
    document_count = db.query(db_entities.Document).filter(db_entities.Document.organization_id == org_id).count()
    settings = parse_json_dict(org.settings_json)
    configured_questions = settings.get("suggested_questions")
    suggested_questions = (
        [str(item).strip() for item in configured_questions if str(item).strip()][:3]
        if isinstance(configured_questions, list)
        else []
    )
    return OrganizationDashboardEntity(
        organization=org,
        employee_count=db.query(db_entities.OrganizationMember).filter(db_entities.OrganizationMember.organization_id == org_id).count(),
        document_count=document_count,
        indexed_document_count=db.query(db_entities.Document)
        .filter(db_entities.Document.organization_id == org_id, db_entities.Document.status.in_(DOCUMENT_INDEXED_STATUSES))
        .count(),
        chat_session_count=db.query(db_entities.ChatSession).filter(db_entities.ChatSession.organization_id == org_id).count(),
        suggested_questions=suggested_questions or [
            "Chinh sach nghi phep cua cong ty la gi?",
            "Quy trinh phe duyet chi phi noi bo nhu the nao?",
            "Nhan vien moi can doc tai lieu nao dau tien?",
        ],
    )
