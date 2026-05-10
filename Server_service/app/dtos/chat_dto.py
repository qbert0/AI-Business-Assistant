from app import models
from app.entities import database as db_entities
from app.entities.chat import ChatAnswerEntity, CitationEntity, ReportArtifactEntity
from app.repositories.common import parse_json_list
from app.services.chat_artifacts import extract_report_artifacts
from app.services.storage import generate_presigned_download_url


def to_citation_model(entity: CitationEntity) -> models.Citation:
    return models.Citation(
        document_id=entity.document_id,
        file_name=entity.file_name,
        source_url=entity.source_url,
    )


def _hydrate_report_artifacts(raw_payloads: list[dict]) -> list[ReportArtifactEntity]:
    hydrated: list[ReportArtifactEntity] = []
    for payload in raw_payloads:
        if not isinstance(payload, dict):
            continue
        bucket = str(payload.get("bucket") or "").strip()
        object_key = str(payload.get("object_key") or "").strip()
        if not bucket or not object_key:
            continue
        file_name = str(payload.get("file_name") or "report.pdf").strip() or "report.pdf"
        hydrated.append(
            ReportArtifactEntity(
                kind="pdf",
                label=str(payload.get("label") or "Xem báo cáo PDF").strip() or "Xem báo cáo PDF",
                file_name=file_name,
                bucket=bucket,
                object_key=object_key,
                source_url=str(payload.get("source_url") or "").strip(),
                content_type=str(payload.get("content_type") or "").strip() or None,
                url=_safe_presign_url(bucket, object_key, file_name),
            )
        )
    return hydrated


def _safe_presign_url(bucket: str, object_key: str, file_name: str) -> str | None:
    try:
        return generate_presigned_download_url(bucket, object_key, file_name=file_name)
    except Exception:
        return None


def to_report_artifact_model(entity: ReportArtifactEntity) -> models.ReportArtifact:
    download_url = entity.url or _safe_presign_url(entity.bucket, entity.object_key, entity.file_name)
    return models.ReportArtifact(
        kind="pdf",
        label=entity.label,
        file_name=entity.file_name,
        source_url=entity.source_url,
        download_url=download_url,
        content_type=entity.content_type,
    )


def to_chat_message_model(message: db_entities.ChatMessage) -> models.ChatMessageRead:
    cleaned_content, artifact_payloads = extract_report_artifacts(message.content)
    return models.ChatMessageRead(
        id=message.id,
        session_id=message.session_id,
        sender_type=message.sender_type,
        content=cleaned_content,
        citations=[models.Citation(**item) for item in parse_json_list(message.citations_json)],
        artifacts=[to_report_artifact_model(item) for item in _hydrate_report_artifacts(artifact_payloads)],
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
    artifacts = [to_report_artifact_model(artifact) for artifact in entity.report_artifacts]
    return models.ChatAnswer(
        session=to_chat_session_model(entity.session),
        user_message=to_chat_message_model(entity.user_message),
        assistant_message=to_chat_message_model(entity.assistant_message),
        answer=entity.answer,
        citations=citations,
        artifacts=artifacts,
        search_hits=[
            models.DocumentSearchHit(
                document_id=hit.document_id,
                file_name=hit.document.get("file_name") or hit.document_id,
                source_url=hit.document.get("source_url") or "",
                score=hit.score,
                document=hit.document,
            )
            for hit in entity.search_hits
        ],
    )
