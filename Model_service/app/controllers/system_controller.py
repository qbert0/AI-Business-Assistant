from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app import models


router = APIRouter(tags=["System"])


@router.get("/", response_model=models.ApiInfo, summary="Thong tin Model Service va Swagger")
def root() -> models.ApiInfo:
    settings = get_settings()
    return models.ApiInfo(
        name=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        health_url="/health",
        capabilities=[
            "provider-registry",
            "model-registry",
            "policy-management",
            "context-builder",
            "inference-orchestration",
            "feedback-tracking",
            "metrics-rollup",
        ],
    )


@router.get("/health", response_model=models.HealthStatus, summary="Kiem tra Model Service dang hoat dong")
def health() -> models.HealthStatus:
    return models.HealthStatus(status="ok", timestamp=datetime.now(timezone.utc))

