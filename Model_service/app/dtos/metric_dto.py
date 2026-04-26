from collections import defaultdict
from datetime import datetime, timezone

from app.entities import database as entities
from app.models.metric_model import MetricSummary, MetricSummaryResponse


def to_metric_summary_response_model(
    rollups: list[entities.MetricRollup],
    bucket_granularity: str = "hour",
) -> MetricSummaryResponse:
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

    for item in rollups:
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
    for model_id, data in aggregates.items():
        request_count = int(data["request_count"])
        avg_latency_ms = round(int(data["total_latency_ms"]) / request_count, 2) if request_count else 0.0
        items.append(
            MetricSummary(
                model_id=model_id,
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
        bucket_granularity=bucket_granularity,
        items=items,
    )

