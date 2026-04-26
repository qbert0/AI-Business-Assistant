from app.entities import database as entities
from app.entities.inference import InferenceResultEntity
from app.models import inference_model


def to_inference_request_model(request: entities.InferenceRequest) -> inference_model.InferenceRequestRead:
    return inference_model.InferenceRequestRead(
        id=request.id,
        conversation_id=request.conversation_id,
        organization_id=request.organization_id,
        user_id=request.user_id,
        model_id=request.model_id,
        policy_id=request.policy_id,
        question=request.question,
        status=request.status,
        latency_ms=request.latency_ms,
        error_message=request.error_message,
        started_at=request.started_at,
        finished_at=request.finished_at,
    )


def to_inference_response_model(response: entities.InferenceResponse) -> inference_model.InferenceResponseRead:
    return inference_model.InferenceResponseRead(
        id=response.id,
        request_id=response.request_id,
        response_text=response.response_text,
        finish_reason=response.finish_reason,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        total_tokens=response.total_tokens,
        estimated_cost=response.estimated_cost,
        created_at=response.created_at,
    )


def to_inference_list_item_model(request: entities.InferenceRequest) -> inference_model.InferenceListItem:
    return inference_model.InferenceListItem(
        request=to_inference_request_model(request),
        response=to_inference_response_model(request.response) if request.response else None,
    )


def to_inference_result_model(entity: InferenceResultEntity) -> inference_model.InferenceResult:
    return inference_model.InferenceResult(
        request=to_inference_request_model(entity.request),
        response=to_inference_response_model(entity.response),
        context=entity.context,
    )

