from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import (
    contexts_controller,
    feedback_controller,
    inferences_controller,
    metrics_controller,
    models_registry_controller,
    providers_controller,
    system_controller,
)
from app.core.config import get_settings
from app.db.session import init_db


settings = get_settings()

tags_metadata = [
    {"name": "System", "description": "Thong tin service va health check."},
    {"name": "Providers", "description": "Quan ly provider cho cac model serving endpoint."},
    {"name": "Registry", "description": "Dang ky model, policy va health check model."},
    {"name": "Contexts", "description": "Assemble context cho query truoc khi inference."},
    {"name": "Inferences", "description": "Thuc hien inference va luu metadata request/response."},
    {"name": "Feedback", "description": "Luu feedback nguoi dung theo model va conversation."},
    {"name": "Metrics", "description": "Thong ke usage, latency, token va chi phi uoc tinh."},
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Model Service cho AI Business Assistant. "
        "Service nay quan ly provider, model registry, context building, inference orchestration, "
        "feedback va metrics tren mot database rieng."
    ),
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(system_controller.router)
app.include_router(providers_controller.router, prefix="/api/v1")
app.include_router(models_registry_controller.router, prefix="/api/v1")
app.include_router(contexts_controller.router, prefix="/api/v1")
app.include_router(inferences_controller.router, prefix="/api/v1")
app.include_router(feedback_controller.router, prefix="/api/v1")
app.include_router(metrics_controller.router, prefix="/api/v1")
