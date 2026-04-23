import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import messages
from app import models
from app.entities import database as db_entities
from app.entities.chat import ChatAnswerEntity, CitationEntity
from app.repositories.common import require_permission
from app.services.search_service import query_documents


def chat_suggestions(org_id: str, acting_user_id: str, db: Session) -> list[str]:
    require_permission(db, org_id, acting_user_id, "chat_advisory")
    return [
        "Thu nhap va phuc loi hien tai gom nhung gi?",
        "Chinh sach nghi phep ap dung ra sao?",
        "Quy trinh noi bo nao lien quan den nhan vien moi?",
    ]


def list_chat_sessions(org_id: str, acting_user_id: str, db: Session) -> list[db_entities.ChatSession]:
    require_permission(db, org_id, acting_user_id, "chat_advisory")
    return (
        db.query(db_entities.ChatSession)
        .filter(db_entities.ChatSession.organization_id == org_id, db_entities.ChatSession.user_id == acting_user_id)
        .order_by(db_entities.ChatSession.updated_at.desc())
        .all()
    )


def create_chat_session(org_id: str, payload: models.ChatSessionCreate, db: Session) -> db_entities.ChatSession:
    require_permission(db, org_id, payload.user_id, "chat_advisory")
    session = db_entities.ChatSession(
        organization_id=org_id,
        user_id=payload.user_id,
        context_type=payload.context_type,
        title=payload.title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_chat_messages(session_id: str, acting_user_id: str, db: Session) -> list[db_entities.ChatMessage]:
    session = db.get(db_entities.ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.SESSION_NOT_FOUND)
    if session.organization_id:
        require_permission(db, session.organization_id, acting_user_id, "chat_advisory")
    elif session.user_id != acting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc xem chat cua user khac.")
    messages_list = (
        db.query(db_entities.ChatMessage)
        .filter(db_entities.ChatMessage.session_id == session_id)
        .order_by(db_entities.ChatMessage.created_at.asc())
        .all()
    )
    return messages_list


def ask_chat(org_id: str, payload: models.ChatAsk, db: Session) -> ChatAnswerEntity:
    require_permission(db, org_id, payload.user_id, "chat_advisory")
    session = db.get(db_entities.ChatSession, payload.session_id) if payload.session_id else None
    if session and session.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.ORGANIZATION_SESSION_MISMATCH)
    if not session:
        title = payload.question[:80]
        session = db_entities.ChatSession(organization_id=org_id, user_id=payload.user_id, context_type="organization", title=title)
        db.add(session)
        db.flush()

    hits = query_documents(f"org-{org_id}-documents", payload.question, size=3)
    citations: list[CitationEntity] = []
    context_lines = []
    for hit in hits:
        document_id = hit.document.get("document_id") or hit.document_id
        citation = CitationEntity(
            document_id=document_id,
            file_name=hit.document.get("file_name") or document_id,
            source_url=hit.document.get("source_url") or "",
        )
        citations.append(citation)
        context_lines.append(f"- {citation.file_name} ({citation.source_url})")

    if context_lines:
        answer = (
            "Ket qua tim kiem tu Elasticsearch cho cau hoi cua ban dang tro toi cac tai lieu phu hop: "
            + " ".join(context_lines)
            + " Ket noi LLM co the dung cac citation nay lam context de sinh cau tra loi day du."
        )
    else:
        answer = "Chua tim thay tai lieu phu hop trong Elasticsearch cho cau hoi nay."

    user_message = db_entities.ChatMessage(session_id=session.id, sender_type="user", content=payload.question)
    assistant_message = db_entities.ChatMessage(
        session_id=session.id,
        sender_type="ai",
        content=answer,
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
        search_hits=hits,
    )


def create_feedback(message_id: str, payload: models.FeedbackCreate, db: Session) -> db_entities.ChatFeedback:
    message = db.get(db_entities.ChatMessage, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message khong ton tai.")
    session = db.get(db_entities.ChatSession, message.session_id)
    if session.organization_id:
        require_permission(db, session.organization_id, payload.user_id, "chat_advisory")
    feedback = db_entities.ChatFeedback(message_id=message_id, user_id=payload.user_id, rating=payload.rating, comment=payload.comment)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def delete_chat_session(session_id: str, acting_user_id: str, db: Session) -> None:
    session = db.get(db_entities.ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.SESSION_NOT_FOUND)
    if session.organization_id:
        require_permission(db, session.organization_id, acting_user_id, "delete_chat_sessions")
    elif session.user_id != acting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc xoa chat cua user khac.")
    db.delete(session)
    db.commit()
