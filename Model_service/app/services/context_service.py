from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.serialization import parse_json_dict, parse_json_list
from app.db import models as db_models
from app.schemas.context import (
    ContextBuildRequest,
    ContextBuildResponse,
    ContextItem,
    ContextSnapshotRead,
    ConversationMessage,
    StoredContextDetail,
    StoredContextPayload,
    StoredContextRead,
)


DEFAULT_SYSTEM_PROMPT = (
    "You are an enterprise financial advisory assistant. "
    "Provide grounded, concise, professional answers. "
    "Use only the trusted context that is supplied. "
    "If the available context is insufficient, say so clearly instead of inventing facts."
)


class ContextService:
    def build_context(self, payload: ContextBuildRequest) -> ContextBuildResponse:
        history = payload.history[-payload.max_history_messages :]
        context_items = payload.external_contexts

        system_parts = [payload.system_prompt or DEFAULT_SYSTEM_PROMPT]
        if payload.organization_id:
            system_parts.append(f"Organization context: {payload.organization_id}.")
        if context_items:
            serialized_items = []
            for index, item in enumerate(context_items, start=1):
                label = f"[{index}] {item.title}"
                if item.source:
                    label = f"{label} ({item.source})"
                serialized_items.append(f"{label}\n{item.content}")
            system_parts.append("Trusted context:\n" + "\n\n".join(serialized_items))

        system_prompt = "\n\n".join(part for part in system_parts if part.strip())
        messages = [ConversationMessage(role="system", content=system_prompt), *history]
        messages.append(ConversationMessage(role="user", content=payload.query))

        token_estimate = sum(max(1, len(message.content) // 4) for message in messages)
        return ContextBuildResponse(
            system_prompt=system_prompt,
            messages=messages,
            context_items=context_items,
            token_estimate=token_estimate,
        )

    def _deserialize_context(self, raw_context: str | None) -> StoredContextPayload:
        data = parse_json_dict(raw_context)
        messages_raw = parse_json_list(data.get("messages"))
        context_items_raw = parse_json_list(data.get("context_items"))
        input_messages_raw = parse_json_list(data.get("input_messages"))
        conversation_messages_raw = parse_json_list(data.get("conversation_messages"))

        messages = [ConversationMessage(**message) for message in messages_raw if isinstance(message, dict)]
        input_messages = [ConversationMessage(**message) for message in input_messages_raw if isinstance(message, dict)]
        conversation_messages = [
            ConversationMessage(**message) for message in conversation_messages_raw if isinstance(message, dict)
        ]
        if not input_messages:
            input_messages = messages
        if not conversation_messages:
            conversation_messages = messages

        return StoredContextPayload(
            system_prompt=str(data.get("system_prompt") or ""),
            messages=messages,
            context_items=[ContextItem(**item) for item in context_items_raw if isinstance(item, dict)],
            token_estimate=int(data.get("token_estimate") or 0),
            input_messages=input_messages,
            conversation_messages=conversation_messages,
            latest_user_message=data.get("latest_user_message"),
            latest_assistant_message=data.get("latest_assistant_message"),
            error_message=data.get("error_message"),
        )

    def _serialize_stored_context(self, request: db_models.InferenceRequest) -> StoredContextRead:
        return StoredContextRead(
            request_id=request.id,
            conversation_id=request.conversation_id,
            organization_id=request.organization_id,
            user_id=request.user_id,
            query=request.question,
            context=self._deserialize_context(request.assembled_context_json),
            created_at=request.started_at,
        )

    def _serialize_snapshot(self, snapshot: db_models.ContextSnapshot) -> ContextSnapshotRead:
        items_raw = parse_json_list(snapshot.items_json)
        return ContextSnapshotRead(
            id=snapshot.id,
            request_id=snapshot.request_id,
            conversation_id=snapshot.conversation_id,
            organization_id=snapshot.organization_id,
            user_id=snapshot.user_id,
            query_text=snapshot.query_text,
            context_items=[ContextItem(**item) for item in items_raw if isinstance(item, dict)],
            token_estimate=snapshot.token_estimate,
            source=snapshot.source,
            created_at=snapshot.created_at,
        )

    def list_stored_contexts(
        self,
        db: Session,
        conversation_id: str | None = None,
        organization_id: str | None = None,
        user_id: str | None = None,
        limit: int = 20,
    ) -> list[StoredContextRead]:
        query = db.query(db_models.InferenceRequest).order_by(db_models.InferenceRequest.started_at.desc())
        if conversation_id:
            query = query.filter(db_models.InferenceRequest.conversation_id == conversation_id)
        if organization_id:
            query = query.filter(db_models.InferenceRequest.organization_id == organization_id)
        if user_id:
            query = query.filter(db_models.InferenceRequest.user_id == user_id)
        return [self._serialize_stored_context(item) for item in query.limit(limit).all()]

    def get_stored_context(self, db: Session, request_id: str) -> StoredContextDetail:
        request = (
            db.query(db_models.InferenceRequest)
            .filter(db_models.InferenceRequest.id == request_id)
            .first()
        )
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored context khong ton tai.")

        snapshots = (
            db.query(db_models.ContextSnapshot)
            .filter(db_models.ContextSnapshot.request_id == request_id)
            .order_by(db_models.ContextSnapshot.created_at.desc())
            .all()
        )
        return StoredContextDetail(
            stored_context=self._serialize_stored_context(request),
            snapshots=[self._serialize_snapshot(item) for item in snapshots],
        )
