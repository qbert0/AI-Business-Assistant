from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import ApiInfo, HealthStatus


router = APIRouter(tags=["System"])


@router.get("/", response_model=ApiInfo, summary="Thong tin Model Service va Swagger")
def root() -> ApiInfo:
    settings = get_settings()
    return ApiInfo(
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


@router.get("/health", response_model=HealthStatus, summary="Kiem tra Model Service dang hoat dong")
def health() -> HealthStatus:
    return HealthStatus(status="ok", timestamp=datetime.now(timezone.utc))
