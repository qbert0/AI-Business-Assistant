from app.core.serialization import parse_json_dict, parse_json_list
from app.entities import database as entities
from app.models.context_model import (
    ContextItem,
    ContextSnapshotRead,
    ConversationMessage,
    StoredContextDetail,
    StoredContextPayload,
    StoredContextRead,
)


def deserialize_context(raw_context: str | None) -> StoredContextPayload:
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


def to_stored_context_model(request: entities.InferenceRequest) -> StoredContextRead:
    return StoredContextRead(
        request_id=request.id,
        conversation_id=request.conversation_id,
        organization_id=request.organization_id,
        user_id=request.user_id,
        query=request.question,
        context=deserialize_context(request.assembled_context_json),
        created_at=request.started_at,
    )


def to_context_snapshot_model(snapshot: entities.ContextSnapshot) -> ContextSnapshotRead:
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


def to_stored_context_detail_model(
    request: entities.InferenceRequest,
    snapshots: list[entities.ContextSnapshot],
) -> StoredContextDetail:
    return StoredContextDetail(
        stored_context=to_stored_context_model(request),
        snapshots=[to_context_snapshot_model(item) for item in snapshots],
    )
