from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app.constants.documents import DOCUMENT_INDEXED_STATUSES
from app.entities.api import AnalyticsEntity
from app.entities import database as db_entities
from app.repositories.common import get_org_or_404, require_permission


def get_analytics(org_id: str, acting_user_id: str, db: Session) -> AnalyticsEntity:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "view_analytics")
    recent_user_messages = (
        db.query(db_entities.ChatMessage)
        .join(db_entities.ChatSession)
        .filter(db_entities.ChatSession.organization_id == org_id, db_entities.ChatMessage.sender_type == "user")
        .order_by(db_entities.ChatMessage.created_at.desc())
        .limit(5)
        .all()
    )
    popular_question_rows = (
        db.query(
            db_entities.ChatMessage.content,
            func.count(db_entities.ChatMessage.id).label("question_count"),
        )
        .join(db_entities.ChatSession)
        .filter(db_entities.ChatSession.organization_id == org_id, db_entities.ChatMessage.sender_type == "user")
        .group_by(db_entities.ChatMessage.content)
        .order_by(func.count(db_entities.ChatMessage.id).desc(), func.max(db_entities.ChatMessage.created_at).desc())
        .limit(10)
        .all()
    )
    feedback_rows = (
        db.query(db_entities.ChatFeedback, db_entities.ChatMessage, db_entities.ChatSession)
        .join(db_entities.ChatMessage, db_entities.ChatFeedback.message_id == db_entities.ChatMessage.id)
        .join(db_entities.ChatSession, db_entities.ChatMessage.session_id == db_entities.ChatSession.id)
        .filter(db_entities.ChatSession.organization_id == org_id, db_entities.ChatMessage.sender_type == "user")
        .order_by(db_entities.ChatFeedback.created_at.desc())
        .limit(25)
        .all()
    )
    feedback_items = []
    for feedback, user_message, session in feedback_rows:
        assistant_message = (
            db.query(db_entities.ChatMessage)
            .filter(
                db_entities.ChatMessage.session_id == user_message.session_id,
                db_entities.ChatMessage.sender_type == "ai",
                db_entities.ChatMessage.created_at >= user_message.created_at,
            )
            .order_by(db_entities.ChatMessage.created_at.asc())
            .first()
        )
        feedback_items.append(
            {
                "id": feedback.id,
                "message_id": feedback.message_id,
                "session_id": session.id,
                "session_title": session.title,
                "question": user_message.content,
                "answer_excerpt": assistant_message.content[:300] if assistant_message else "",
                "rating": feedback.rating,
                "comment": feedback.comment or "",
                "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
            }
        )
    positive_feedback_count = sum(1 for item in feedback_items if item["rating"] == "positive")
    negative_feedback_count = sum(1 for item in feedback_items if item["rating"] == "negative")
    return AnalyticsEntity(
        organization_id=org_id,
        employee_count=db.query(db_entities.OrganizationMember).filter(db_entities.OrganizationMember.organization_id == org_id).count(),
        document_count=db.query(db_entities.Document).filter(db_entities.Document.organization_id == org_id).count(),
        indexed_document_count=db.query(db_entities.Document)
        .filter(db_entities.Document.organization_id == org_id, db_entities.Document.status.in_(DOCUMENT_INDEXED_STATUSES))
        .count(),
        chat_session_count=db.query(db_entities.ChatSession).filter(db_entities.ChatSession.organization_id == org_id).count(),
        question_count=db.query(db_entities.ChatMessage)
        .join(db_entities.ChatSession)
        .filter(db_entities.ChatSession.organization_id == org_id, db_entities.ChatMessage.sender_type == "user")
        .count(),
        popular_questions=[message.content for message in recent_user_messages],
        popular_question_stats=[
            {"question": question, "count": count}
            for question, count in popular_question_rows
        ],
        feedback_summary={
            "total": len(feedback_items),
            "positive": positive_feedback_count,
            "negative": negative_feedback_count,
            "unresolved": negative_feedback_count,
        },
        feedback_items=feedback_items,
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
