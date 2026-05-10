from datetime import datetime, timedelta, timezone

from sqlalchemy.dialects.mysql import insert as mysql_insert
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
        table = db_models.MetricRollup.__table__
        insert_stmt = mysql_insert(table).values(
            model_id=model_id,
            bucket_start=bucket_start,
            bucket_granularity="hour",
            request_count=1,
            success_count=1 if success else 0,
            error_count=0 if success else 1,
            avg_latency_ms=float(latency_ms),
            total_latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=round(float(estimated_cost), 6),
        )
        update_stmt = insert_stmt.on_duplicate_key_update(
            request_count=table.c.request_count + 1,
            success_count=table.c.success_count + (1 if success else 0),
            error_count=table.c.error_count + (0 if success else 1),
            total_latency_ms=table.c.total_latency_ms + latency_ms,
            avg_latency_ms=(
                (table.c.total_latency_ms + latency_ms) / (table.c.request_count + 1)
            ),
            prompt_tokens=table.c.prompt_tokens + prompt_tokens,
            completion_tokens=table.c.completion_tokens + completion_tokens,
            total_tokens=table.c.total_tokens + total_tokens,
            estimated_cost=table.c.estimated_cost + round(float(estimated_cost), 6),
        )
        self.db.execute(update_stmt)

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
