from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dtos import chat_dto
from app.services import ChatService

router = APIRouter()


@router.get("/organizations/{org_id}/chat/suggestions", response_model=list[str], tags=["Chat"], summary="Lay goi y cau hoi theo to chuc")
def chat_suggestions(org_id: str, acting_user_id: str, db: Session = Depends(get_db)) -> list[str]:
    return ChatService(db).chat_suggestions(org_id, acting_user_id)


@router.get("/chat/personal/suggestions", response_model=list[str], tags=["Chat"], summary="Lay goi y cau hoi theo workspace ca nhan")
def personal_chat_suggestions(acting_user_id: str, db: Session = Depends(get_db)) -> list[str]:
    return ChatService(db).personal_chat_suggestions(acting_user_id)


@router.get("/organizations/{org_id}/chat/sessions", response_model=list[models.ChatSessionRead], tags=["Chat"], summary="Lay chat history theo context to chuc")
def list_chat_sessions(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen chat_advisory."),
    db: Session = Depends(get_db),
) -> list[models.ChatSessionRead]:
    return chat_dto.to_chat_session_models(ChatService(db).list_chat_sessions(org_id, acting_user_id))


@router.get("/chat/personal/sessions", response_model=list[models.ChatSessionRead], tags=["Chat"], summary="Lay chat history theo workspace ca nhan")
def list_personal_chat_sessions(
    acting_user_id: str = Query(..., description="User dang xem workspace ca nhan."),
    db: Session = Depends(get_db),
) -> list[models.ChatSessionRead]:
    return chat_dto.to_chat_session_models(ChatService(db).list_personal_chat_sessions(acting_user_id))


@router.post("/organizations/{org_id}/chat/sessions", response_model=models.ChatSessionRead, status_code=status.HTTP_201_CREATED, tags=["Chat"], summary="Tao chat session rong")
def create_chat_session(org_id: str, payload: models.ChatSessionCreate, db: Session = Depends(get_db)) -> models.ChatSessionRead:
    session = ChatService(db).create_chat_session(org_id, payload)
    return chat_dto.to_chat_session_model(session)


@router.get("/chat/sessions/{session_id}/messages", response_model=list[models.ChatMessageRead], tags=["Chat"], summary="Lay message trong mot chat session")
def list_chat_messages(
    session_id: str,
    acting_user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> list[models.ChatMessageRead]:
    return chat_dto.to_chat_message_models(ChatService(db).list_chat_messages(session_id, acting_user_id))


@router.post("/organizations/{org_id}/chat/ask", response_model=models.ChatAnswer, tags=["Chat"], summary="Hoi dap theo tai lieu noi bo to chuc")
def ask_chat(org_id: str, payload: models.ChatAsk, db: Session = Depends(get_db)) -> models.ChatAnswer:
    result = ChatService(db).ask_chat(org_id, payload)
    return chat_dto.to_chat_answer_model(result)


@router.post("/chat/personal/ask", response_model=models.ChatAnswer, tags=["Chat"], summary="Hoi dap theo workspace ca nhan")
def ask_personal_chat(payload: models.ChatAsk, db: Session = Depends(get_db)) -> models.ChatAnswer:
    result = ChatService(db).ask_personal_chat(payload)
    return chat_dto.to_chat_answer_model(result)


@router.post("/organizations/{org_id}/chat/ask/stream", tags=["Chat"], summary="Hoi dap theo tai lieu noi bo to chuc voi stream")
def stream_chat(org_id: str, payload: models.ChatAsk, db: Session = Depends(get_db)):
    return ChatService(db).stream_chat(org_id, payload)


@router.post("/chat/personal/ask/stream", tags=["Chat"], summary="Hoi dap workspace ca nhan voi stream")
def stream_personal_chat(payload: models.ChatAsk, db: Session = Depends(get_db)):
    return ChatService(db).stream_personal_chat(payload)


@router.post("/chat/messages/{message_id}/feedback", response_model=models.FeedbackRead, status_code=status.HTTP_201_CREATED, tags=["Chat"], summary="Gui feedback cho cau tra loi")
def create_feedback(message_id: str, payload: models.FeedbackCreate, db: Session = Depends(get_db)) -> models.FeedbackRead:
    feedback = ChatService(db).create_feedback(message_id, payload)
    return chat_dto.to_feedback_model(feedback)


@router.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chat"], summary="Xoa mot doan chat")
def delete_chat_session(
    session_id: str,
    acting_user_id: str = Query(..., description="User thuc hien thao tac xoa."),
    db: Session = Depends(get_db),
) -> None:
    ChatService(db).delete_chat_session(session_id, acting_user_id)
