from sqlalchemy.orm import Session

from app import models
from app.entities.api import AnalyticsEntity
from app.entities import database as db_entities
from app.repositories.common import get_org_or_404, require_permission


def get_analytics(org_id: str, acting_user_id: str, db: Session) -> AnalyticsEntity:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "view_analytics")
    user_messages = (
        db.query(db_entities.ChatMessage)
        .join(db_entities.ChatSession)
        .filter(db_entities.ChatSession.organization_id == org_id, db_entities.ChatMessage.sender_type == "user")
        .order_by(db_entities.ChatMessage.created_at.desc())
        .limit(5)
        .all()
    )
    return AnalyticsEntity(
        organization_id=org_id,
        employee_count=db.query(db_entities.OrganizationMember).filter(db_entities.OrganizationMember.organization_id == org_id).count(),
        document_count=db.query(db_entities.Document).filter(db_entities.Document.organization_id == org_id).count(),
        indexed_document_count=db.query(db_entities.Document)
        .filter(db_entities.Document.organization_id == org_id, db_entities.Document.status == "completed")
        .count(),
        chat_session_count=db.query(db_entities.ChatSession).filter(db_entities.ChatSession.organization_id == org_id).count(),
        question_count=db.query(db_entities.ChatMessage)
        .join(db_entities.ChatSession)
        .filter(db_entities.ChatSession.organization_id == org_id, db_entities.ChatMessage.sender_type == "user")
        .count(),
        popular_questions=[message.content for message in user_messages],
        sensitive_restrictions=org.sensitive_restrictions,
    )


def update_restrictions(
    org_id: str,
    payload: models.RestrictionUpdate,
    acting_user_id: str,
    db: Session,
) -> AnalyticsEntity:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "edit_sensitive_restrictions")
    org.sensitive_restrictions = payload.sensitive_restrictions
    db.commit()
    return get_analytics(org_id, acting_user_id, db)
