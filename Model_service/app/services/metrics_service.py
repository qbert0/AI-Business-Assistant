from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session, joinedload

from app.db import models as db_models
from app.schemas.metric import MetricSummary, MetricSummaryResponse


class MetricsService:
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
        rollup = (
            self.db.query(db_models.MetricRollup)
            .filter(
                db_models.MetricRollup.model_id == model_id,
                db_models.MetricRollup.bucket_start == bucket_start,
                db_models.MetricRollup.bucket_granularity == "hour",
            )
            .first()
        )
        if not rollup:
            rollup = db_models.MetricRollup(
                model_id=model_id,
                bucket_start=bucket_start,
                bucket_granularity="hour",
            )
            self.db.add(rollup)
            self.db.flush()

        new_request_count = int(rollup.request_count or 0) + 1
        new_total_latency = int(rollup.total_latency_ms or 0) + latency_ms
        rollup.request_count = new_request_count
        rollup.success_count = int(rollup.success_count or 0) + (1 if success else 0)
        rollup.error_count = int(rollup.error_count or 0) + (0 if success else 1)
        rollup.total_latency_ms = new_total_latency
        rollup.avg_latency_ms = round(new_total_latency / new_request_count, 2)
        rollup.prompt_tokens = int(rollup.prompt_tokens or 0) + prompt_tokens
        rollup.completion_tokens = int(rollup.completion_tokens or 0) + completion_tokens
        rollup.total_tokens = int(rollup.total_tokens or 0) + total_tokens
        rollup.estimated_cost = round(float(rollup.estimated_cost or 0.0) + estimated_cost, 6)

    def summarize(self, hours: int = 24, model_id: str | None = None) -> MetricSummaryResponse:
        threshold = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        query = (
            self.db.query(db_models.MetricRollup)
            .options(joinedload(db_models.MetricRollup.model))
            .filter(db_models.MetricRollup.bucket_start >= threshold)
        )
        if model_id:
            query = query.filter(db_models.MetricRollup.model_id == model_id)

        aggregates: dict[str, dict[str, float | int | str]] = defaultdict(
            lambda: {
                "model_display_name": "",
                "request_count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_latency_ms": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
            }
        )

        for item in query.all():
            bucket = aggregates[item.model_id]
            bucket["model_display_name"] = item.model.display_name if item.model else item.model_id
            bucket["request_count"] += int(item.request_count or 0)
            bucket["success_count"] += int(item.success_count or 0)
            bucket["error_count"] += int(item.error_count or 0)
            bucket["total_latency_ms"] += int(item.total_latency_ms or 0)
            bucket["prompt_tokens"] += int(item.prompt_tokens or 0)
            bucket["completion_tokens"] += int(item.completion_tokens or 0)
            bucket["total_tokens"] += int(item.total_tokens or 0)
            bucket["estimated_cost"] += float(item.estimated_cost or 0.0)

        items = []
        for current_model_id, data in aggregates.items():
            request_count = int(data["request_count"])
            avg_latency_ms = round(int(data["total_latency_ms"]) / request_count, 2) if request_count else 0.0
            items.append(
                MetricSummary(
                    model_id=current_model_id,
                    model_display_name=str(data["model_display_name"]),
                    request_count=request_count,
                    success_count=int(data["success_count"]),
                    error_count=int(data["error_count"]),
                    avg_latency_ms=avg_latency_ms,
                    prompt_tokens=int(data["prompt_tokens"]),
                    completion_tokens=int(data["completion_tokens"]),
                    total_tokens=int(data["total_tokens"]),
                    estimated_cost=round(float(data["estimated_cost"]), 6),
                )
            )

        items.sort(key=lambda item: (-item.request_count, item.model_display_name))
        return MetricSummaryResponse(
            generated_at=datetime.now(timezone.utc),
            bucket_granularity="hour",
            items=items,
        )
