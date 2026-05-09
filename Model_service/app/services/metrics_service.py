from app.models.metric_model import MetricSummaryResponse
from app.repositories.metrics_repository import MetricsRepository


class MetricsService:
    def __init__(self, repository: MetricsRepository) -> None:
        self.repository = repository

    @classmethod
    def from_db(cls, db) -> "MetricsService":
        return cls(MetricsRepository(db))

    def summarize(self, *, hours: int = 24, model_id: str | None = None) -> MetricSummaryResponse:
        return self.repository.summarize(hours=hours, model_id=model_id)
