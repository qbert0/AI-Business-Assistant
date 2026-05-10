import json

from sqlalchemy.orm import Session

from app.entities import database as db_entities
from app.entities.chat import ChatAnswerEntity, CitationEntity, ReportArtifactEntity
from app.entities.search import SearchHitEntity
from app.services.chat_artifacts import serialize_report_artifacts


def get_chat_session(session_id: str, db: Session) -> db_entities.ChatSession | None:
    return db.get(db_entities.ChatSession, session_id)


def list_chat_sessions(org_id: str, acting_user_id: str, db: Session) -> list[db_entities.ChatSession]:
    return (
        db.query(db_entities.ChatSession)
        .filter(db_entities.ChatSession.organization_id == org_id, db_entities.ChatSession.user_id == acting_user_id)
        .order_by(db_entities.ChatSession.updated_at.desc())
        .all()
    )


def list_personal_chat_sessions(acting_user_id: str, db: Session) -> list[db_entities.ChatSession]:
    return (
        db.query(db_entities.ChatSession)
        .filter(db_entities.ChatSession.organization_id.is_(None), db_entities.ChatSession.user_id == acting_user_id)
        .order_by(db_entities.ChatSession.updated_at.desc())
        .all()
    )


def create_chat_session(
    org_id: str | None,
    user_id: str,
    context_type: str,
    title: str,
    db: Session,
) -> db_entities.ChatSession:
    session = db_entities.ChatSession(
        organization_id=org_id,
        user_id=user_id,
        context_type=context_type,
        title=title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_chat_messages(session_id: str, db: Session) -> list[db_entities.ChatMessage]:
    return (
        db.query(db_entities.ChatMessage)
        .filter(db_entities.ChatMessage.session_id == session_id)
        .order_by(db_entities.ChatMessage.created_at.asc())
        .all()
    )


def list_chat_history(session_id: str, db: Session, limit: int = 12) -> list[db_entities.ChatMessage]:
    messages = (
        db.query(db_entities.ChatMessage)
        .filter(db_entities.ChatMessage.session_id == session_id)
        .order_by(db_entities.ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))


def list_chat_feedback_history(
    session_id: str,
    db: Session,
    limit: int = 6,
) -> list[tuple[db_entities.ChatFeedback, db_entities.ChatMessage]]:
    rows = (
        db.query(db_entities.ChatFeedback, db_entities.ChatMessage)
        .join(db_entities.ChatMessage, db_entities.ChatFeedback.message_id == db_entities.ChatMessage.id)
        .filter(
            db_entities.ChatMessage.session_id == session_id,
            db_entities.ChatMessage.sender_type == "ai",
        )
        .order_by(db_entities.ChatFeedback.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def save_chat_answer(
    session: db_entities.ChatSession,
    question: str,
    answer: str,
    citations: list[CitationEntity],
    search_hits: list[SearchHitEntity],
    report_artifacts: list[ReportArtifactEntity],
    db: Session,
) -> ChatAnswerEntity:
    user_message = db_entities.ChatMessage(session_id=session.id, sender_type="user", content=question)
    assistant_message = db_entities.ChatMessage(
        session_id=session.id,
        sender_type="ai",
        content=serialize_report_artifacts(answer, report_artifacts),
        citations_json=json.dumps(
            [
                {
                    "document_id": citation.document_id,
                    "file_name": citation.file_name,
                    "source_url": citation.source_url,
                }
                for citation in citations
            ]
        ),
    )
    db.add_all([user_message, assistant_message])
    db.commit()
    db.refresh(session)
    db.refresh(user_message)
    db.refresh(assistant_message)
    return ChatAnswerEntity(
        session=session,
        user_message=user_message,
        assistant_message=assistant_message,
        answer=answer,
        citations=citations,
        search_hits=search_hits,
        report_artifacts=report_artifacts,
    )


def create_feedback(message_id: str, user_id: str, rating: str, comment: str | None, db: Session) -> db_entities.ChatFeedback:
    feedback = db_entities.ChatFeedback(message_id=message_id, user_id=user_id, rating=rating, comment=comment)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def delete_chat_session(session: db_entities.ChatSession, db: Session) -> None:
    db.delete(session)
    db.commit()
