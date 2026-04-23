from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dtos import chat_dto
from app.entities import database as db_entities
from app.repositories import chat_repository

router = APIRouter()


@router.get("/organizations/{org_id}/chat/suggestions", response_model=list[str], tags=["Chat"], summary="Lay goi y cau hoi theo to chuc")
def chat_suggestions(org_id: str, acting_user_id: str, db: Session = Depends(get_db)) -> list[str]:
    return chat_repository.chat_suggestions(org_id, acting_user_id, db)


@router.get("/organizations/{org_id}/chat/sessions", response_model=list[models.ChatSessionRead], tags=["Chat"], summary="Lay chat history theo context to chuc")
def list_chat_sessions(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen chat_advisory."),
    db: Session = Depends(get_db),
) -> list[models.ChatSessionRead]:
    sessions = chat_repository.list_chat_sessions(org_id, acting_user_id, db)
    return chat_dto.to_chat_session_models(sessions)


@router.post("/organizations/{org_id}/chat/sessions", response_model=models.ChatSessionRead, status_code=status.HTTP_201_CREATED, tags=["Chat"], summary="Tao chat session rong")
def create_chat_session(org_id: str, payload: models.ChatSessionCreate, db: Session = Depends(get_db)) -> models.ChatSessionRead:
    session = chat_repository.create_chat_session(org_id, payload, db)
    return chat_dto.to_chat_session_model(session)


@router.get("/chat/sessions/{session_id}/messages", response_model=list[models.ChatMessageRead], tags=["Chat"], summary="Lay message trong mot chat session")
def list_chat_messages(
    session_id: str,
    acting_user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> list[models.ChatMessageRead]:
    messages = chat_repository.list_chat_messages(session_id, acting_user_id, db)
    return chat_dto.to_chat_message_models(messages)


@router.post("/organizations/{org_id}/chat/ask", response_model=models.ChatAnswer, tags=["Chat"], summary="Hoi dap theo tai lieu noi bo to chuc")
def ask_chat(org_id: str, payload: models.ChatAsk, db: Session = Depends(get_db)) -> models.ChatAnswer:
    answer = chat_repository.ask_chat(org_id, payload, db)
    return chat_dto.to_chat_answer_model(answer)


@router.post("/chat/messages/{message_id}/feedback", response_model=models.FeedbackRead, status_code=status.HTTP_201_CREATED, tags=["Chat"], summary="Gui feedback cho cau tra loi")
def create_feedback(message_id: str, payload: models.FeedbackCreate, db: Session = Depends(get_db)) -> models.FeedbackRead:
    feedback = chat_repository.create_feedback(message_id, payload, db)
    return chat_dto.to_feedback_model(feedback)


@router.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chat"], summary="Xoa mot doan chat")
def delete_chat_session(
    session_id: str,
    acting_user_id: str = Query(..., description="User thuc hien thao tac xoa."),
    db: Session = Depends(get_db),
) -> None:
    return chat_repository.delete_chat_session(session_id, acting_user_id, db)
