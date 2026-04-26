from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db import models as db_models
from app.dtos.context_dto import (
    deserialize_context,
    to_context_snapshot_model,
    to_stored_context_detail_model,
    to_stored_context_model,
)
from app.models.context_model import (
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


class ContextRepository:
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
        return deserialize_context(raw_context)

    def _serialize_stored_context(self, request: db_models.InferenceRequest) -> StoredContextRead:
        return to_stored_context_model(request)

    def _serialize_snapshot(self, snapshot: db_models.ContextSnapshot) -> ContextSnapshotRead:
        return to_context_snapshot_model(snapshot)

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
        return to_stored_context_detail_model(request, snapshots)

