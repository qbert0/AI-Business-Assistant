from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.core.security import decrypt_secret
from app.core.serialization import dump_json, parse_json_dict
from app.db import models as db_models
from app.infrastructure.llm.base import LLMResult, ProviderRequestError
from app.infrastructure.llm.factory import build_llm_client
from app.schemas.context import ContextBuildRequest, ContextBuildResponse
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.schemas.inference import (
    InferenceCreate,
    InferenceListItem,
    InferenceRequestRead,
    InferenceResponseRead,
    InferenceResult,
)
from app.services.context_service import ContextService
from app.services.metrics_service import MetricsService
from app.services.registry_service import RegistryService


class InferenceService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.registry_service = RegistryService(db, settings)
        self.context_service = ContextService()
        self.metrics_service = MetricsService(db)

    def _serialize_request(self, request: db_models.InferenceRequest) -> InferenceRequestRead:
        return InferenceRequestRead(
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

    def _serialize_response(self, response: db_models.InferenceResponse) -> InferenceResponseRead:
        return InferenceResponseRead(
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

    def _serialize_feedback(self, feedback: db_models.FeedbackEvent) -> FeedbackRead:
        return FeedbackRead(
            id=feedback.id,
            request_id=feedback.request_id,
            conversation_id=feedback.conversation_id,
            organization_id=feedback.organization_id,
            user_id=feedback.user_id,
            model_id=feedback.model_id,
            rating=feedback.rating,
            comment=feedback.comment,
            metadata=parse_json_dict(feedback.metadata_json),
            created_at=feedback.created_at,
        )

    def list_inferences(
        self,
        conversation_id: str | None = None,
        organization_id: str | None = None,
        user_id: str | None = None,
        limit: int = 20,
    ) -> list[InferenceListItem]:
        query = (
            self.db.query(db_models.InferenceRequest)
            .options(joinedload(db_models.InferenceRequest.response))
            .order_by(db_models.InferenceRequest.started_at.desc())
        )
        if conversation_id:
            query = query.filter(db_models.InferenceRequest.conversation_id == conversation_id)
        if organization_id:
            query = query.filter(db_models.InferenceRequest.organization_id == organization_id)
        if user_id:
            query = query.filter(db_models.InferenceRequest.user_id == user_id)

        items = []
        for request in query.limit(limit).all():
            items.append(
                InferenceListItem(
                    request=self._serialize_request(request),
                    response=self._serialize_response(request.response) if request.response else None,
                )
            )
        return items

    def get_inference(self, request_id: str) -> InferenceListItem:
        request = (
            self.db.query(db_models.InferenceRequest)
            .options(joinedload(db_models.InferenceRequest.response))
            .filter(db_models.InferenceRequest.id == request_id)
            .first()
        )
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inference request khong ton tai.")
        return InferenceListItem(
            request=self._serialize_request(request),
            response=self._serialize_response(request.response) if request.response else None,
        )

    def _estimate_cost(
        self,
        model: db_models.RegisteredModel,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        parameters = parse_json_dict(model.parameters_json)
        pricing = parameters.get("pricing") if isinstance(parameters.get("pricing"), dict) else {}
        prompt_per_1k = float(pricing.get("prompt_per_1k") or 0.0)
        completion_per_1k = float(pricing.get("completion_per_1k") or 0.0)
        total = (prompt_tokens / 1000.0) * prompt_per_1k + (completion_tokens / 1000.0) * completion_per_1k
        return round(total, 6)

    def _run_candidate(
        self,
        model: db_models.RegisteredModel,
        context: ContextBuildResponse,
        temperature: float,
        max_tokens: int,
        metadata: dict,
    ) -> LLMResult:
        client = build_llm_client(
            model,
            decrypt_secret(model.api_key_encrypted, self.settings),
            self.settings.default_provider_timeout_seconds,
        )
        messages = [message.dict() for message in context.messages]
        return client.chat(messages=messages, temperature=temperature, max_tokens=max_tokens, metadata=metadata)

    def _run_with_fallback(
        self,
        model: db_models.RegisteredModel,
        policy: db_models.ModelPolicy | None,
        context: ContextBuildResponse,
        temperature: float,
        max_tokens: int,
        metadata: dict,
    ) -> tuple[db_models.RegisteredModel, LLMResult]:
        candidates = [model]
        if policy and policy.fallback_model and policy.fallback_model.is_active and policy.fallback_model.id != model.id:
            candidates.append(policy.fallback_model)

        errors = []
        for candidate in candidates:
            try:
                return candidate, self._run_candidate(candidate, context, temperature, max_tokens, metadata)
            except (ProviderRequestError, ValueError) as exc:
                errors.append(f"{candidate.display_name}: {exc}")

        raise ProviderRequestError("; ".join(errors) if errors else "No candidate model was available.")

    def create_inference(self, payload: InferenceCreate) -> InferenceResult:
        model, policy = self.registry_service.resolve_model(payload.model_id, payload.organization_id, payload.use_case)
        resolved_temperature = payload.temperature if payload.temperature is not None else (policy.temperature if policy else 0.2)
        resolved_max_tokens = payload.max_tokens if payload.max_tokens is not None else (policy.max_tokens if policy else 1200)
        resolved_system_prompt = payload.system_prompt or (policy.system_prompt if policy else None)

        context = self.context_service.build_context(
            ContextBuildRequest(
                conversation_id=payload.conversation_id,
                organization_id=payload.organization_id,
                user_id=payload.user_id,
                query=payload.question,
                history=payload.history,
                external_contexts=payload.external_contexts,
                system_prompt=resolved_system_prompt,
            )
        )

        request_record = db_models.InferenceRequest(
            conversation_id=payload.conversation_id,
            organization_id=payload.organization_id,
            user_id=payload.user_id,
            model_id=model.id,
            policy_id=policy.id if policy else None,
            question=payload.question,
            request_payload_json=dump_json(payload.dict()),
            assembled_context_json=dump_json(context.dict()),
            status="running",
        )
        self.db.add(request_record)
        self.db.flush()

        snapshot = db_models.ContextSnapshot(
            conversation_id=payload.conversation_id,
            organization_id=payload.organization_id,
            user_id=payload.user_id,
            request_id=request_record.id,
            query_text=payload.question,
            items_json=dump_json([item.dict() for item in context.context_items]),
            token_estimate=context.token_estimate,
            source="assembled",
        )
        self.db.add(snapshot)
        self.db.flush()

        started_at = datetime.now(timezone.utc)
        try:
            used_model, output = self._run_with_fallback(
                model=model,
                policy=policy,
                context=context,
                temperature=resolved_temperature,
                max_tokens=resolved_max_tokens,
                metadata=payload.metadata,
            )
            finished_at = datetime.now(timezone.utc)
            latency_ms = max(1, int((finished_at - started_at).total_seconds() * 1000))
            estimated_cost = self._estimate_cost(used_model, output.prompt_tokens, output.completion_tokens)

            request_record.model_id = used_model.id
            request_record.status = "completed"
            request_record.finished_at = finished_at
            request_record.latency_ms = latency_ms
            request_record.error_message = None

            response_record = db_models.InferenceResponse(
                request_id=request_record.id,
                response_text=output.response_text,
                finish_reason=output.finish_reason,
                raw_response_json=dump_json(output.raw_response),
                prompt_tokens=output.prompt_tokens,
                completion_tokens=output.completion_tokens,
                total_tokens=output.total_tokens,
                estimated_cost=estimated_cost,
            )
            self.db.add(response_record)
            self.metrics_service.record_inference(
                model_id=used_model.id,
                finished_at=finished_at,
                latency_ms=latency_ms,
                success=True,
                prompt_tokens=output.prompt_tokens,
                completion_tokens=output.completion_tokens,
                total_tokens=output.total_tokens,
                estimated_cost=estimated_cost,
            )
            self.db.commit()
            self.db.refresh(request_record)
            self.db.refresh(response_record)
            return InferenceResult(
                request=self._serialize_request(request_record),
                response=self._serialize_response(response_record),
                context=context,
            )
        except (ProviderRequestError, ValueError) as exc:
            finished_at = datetime.now(timezone.utc)
            latency_ms = max(1, int((finished_at - started_at).total_seconds() * 1000))
            request_record.status = "failed"
            request_record.finished_at = finished_at
            request_record.latency_ms = latency_ms
            request_record.error_message = str(exc)
            self.metrics_service.record_inference(
                model_id=model.id,
                finished_at=finished_at,
                latency_ms=latency_ms,
                success=False,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                estimated_cost=0.0,
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Khong the goi model upstream: {exc}",
            ) from exc

    def create_feedback(self, payload: FeedbackCreate) -> FeedbackRead:
        resolved_model_id = payload.model_id
        if payload.request_id:
            request = self.db.get(db_models.InferenceRequest, payload.request_id)
            if not request:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inference request khong ton tai.")
            resolved_model_id = resolved_model_id or request.model_id

        feedback = db_models.FeedbackEvent(
            request_id=payload.request_id,
            conversation_id=payload.conversation_id,
            organization_id=payload.organization_id,
            user_id=payload.user_id,
            model_id=resolved_model_id,
            rating=payload.rating,
            comment=payload.comment,
            metadata_json=dump_json(payload.metadata),
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return self._serialize_feedback(feedback)

    def list_feedback(
        self,
        organization_id: str | None = None,
        conversation_id: str | None = None,
        model_id: str | None = None,
        limit: int = 50,
    ) -> list[FeedbackRead]:
        query = self.db.query(db_models.FeedbackEvent).order_by(db_models.FeedbackEvent.created_at.desc())
        if organization_id:
            query = query.filter(db_models.FeedbackEvent.organization_id == organization_id)
        if conversation_id:
            query = query.filter(db_models.FeedbackEvent.conversation_id == conversation_id)
        if model_id:
            query = query.filter(db_models.FeedbackEvent.model_id == model_id)
        return [self._serialize_feedback(item) for item in query.limit(limit).all()]
