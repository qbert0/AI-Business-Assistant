from datetime import datetime, timedelta, timezone

from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session, joinedload

from app.db import models as db_models
from app.dtos.metric_dto import to_metric_summary_response_model
from app.models.metric_model import MetricSummaryResponse


class MetricsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_inference(
        self,
        model_id: str,
        finished_at: datetime,
        latency_ms: int,
        success: bool,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        estimated_cost: float,
    ) -> None:
        bucket_start = finished_at.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None)
        request_increment = 1
        success_increment = 1 if success else 0
        error_increment = 0 if success else 1

        stmt = insert(db_models.MetricRollup).values(
            model_id=model_id,
            bucket_start=bucket_start,
            bucket_granularity="hour",
            request_count=request_increment,
            success_count=success_increment,
            error_count=error_increment,
            total_latency_ms=latency_ms,
            avg_latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
        )
        rollup = db_models.MetricRollup
        next_request_count = rollup.request_count + request_increment
        next_total_latency = rollup.total_latency_ms + latency_ms
        self.db.execute(
            stmt.on_duplicate_key_update(
                request_count=next_request_count,
                success_count=rollup.success_count + success_increment,
                error_count=rollup.error_count + error_increment,
                total_latency_ms=next_total_latency,
                avg_latency_ms=next_total_latency / next_request_count,
                prompt_tokens=rollup.prompt_tokens + prompt_tokens,
                completion_tokens=rollup.completion_tokens + completion_tokens,
                total_tokens=rollup.total_tokens + total_tokens,
                estimated_cost=rollup.estimated_cost + estimated_cost,
            )
        )

    def summarize(self, hours: int = 24, model_id: str | None = None) -> MetricSummaryResponse:
        threshold = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        query = (
            self.db.query(db_models.MetricRollup)
            .options(joinedload(db_models.MetricRollup.model))
            .filter(db_models.MetricRollup.bucket_start >= threshold)
        )
        if model_id:
            query = query.filter(db_models.MetricRollup.model_id == model_id)

        return to_metric_summary_response_model(query.all(), bucket_granularity="hour")
