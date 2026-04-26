from datetime import datetime

from pydantic import BaseModel


class MetricSummary(BaseModel):
    model_id: str
    model_display_name: str
    request_count: int
    success_count: int
    error_count: int
    avg_latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float


class MetricSummaryResponse(BaseModel):
    generated_at: datetime
    bucket_granularity: str
    items: list[MetricSummary]
