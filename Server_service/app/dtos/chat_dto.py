from app import models
from app.entities import database as db_entities
from app.entities.chat import ChatAnswerEntity, CitationEntity
from app.repositories.common import parse_json_list


def to_citation_model(entity: CitationEntity) -> models.Citation:
    return models.Citation(
        document_id=entity.document_id,
        file_name=entity.file_name,
        source_url=entity.source_url,
    )


def to_chat_message_model(message: db_entities.ChatMessage) -> models.ChatMessageRead:
    return models.ChatMessageRead(
        id=message.id,
        session_id=message.session_id,
        sender_type=message.sender_type,
        content=message.content,
        citations=[models.Citation(**item) for item in parse_json_list(message.citations_json)],
        created_at=message.created_at,
    )


def to_chat_message_models(messages: list[db_entities.ChatMessage]) -> list[models.ChatMessageRead]:
    return [to_chat_message_model(message) for message in messages]


def to_chat_session_model(session: db_entities.ChatSession) -> models.ChatSessionRead:
    return models.ChatSessionRead(
        id=session.id,
        organization_id=session.organization_id,
        user_id=session.user_id,
        context_type=session.context_type,
        title=session.title,
        is_pinned=session.is_pinned,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def to_chat_session_models(sessions: list[db_entities.ChatSession]) -> list[models.ChatSessionRead]:
    return [to_chat_session_model(session) for session in sessions]


def to_feedback_model(feedback: db_entities.ChatFeedback) -> models.FeedbackRead:
    return models.FeedbackRead(
        id=feedback.id,
        message_id=feedback.message_id,
        user_id=feedback.user_id,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
    )


def to_chat_answer_model(entity: ChatAnswerEntity) -> models.ChatAnswer:
    citations = [to_citation_model(citation) for citation in entity.citations]
    return models.ChatAnswer(
        session=to_chat_session_model(entity.session),
        user_message=to_chat_message_model(entity.user_message),
        assistant_message=to_chat_message_model(entity.assistant_message),
        answer=entity.answer,
        citations=citations,
    )
