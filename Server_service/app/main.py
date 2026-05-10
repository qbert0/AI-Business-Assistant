from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.constants.openapi import TAGS_METADATA
from app.controllers import (
    analytics_controller,
    auth_controller,
    billing_controller,
    chat_controller,
    documents_controller,
    members_controller,
    notifications_controller,
    organizations_controller,
    settings_controller,
    system_controller,
    users_controller,
)
from app.config import CORS_ALLOWED_ORIGIN_REGEX, CORS_ALLOWED_ORIGINS
from app.database import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Business Assistant API",
        description=(
            "Backend API cho AI Business Assistant. He thong ho tro nguoi dung ca nhan, "
            "to chuc, nhan vien, RBAC, quan ly tai lieu, pipeline multi-agent, chat RAG, "
            "analytics va notification. Mo Swagger UI tai `/docs`."
        ),
        version="1.0.0",
        openapi_tags=TAGS_METADATA,
        contact={"name": "AI Business Assistant"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOWED_ORIGINS,
        allow_origin_regex=CORS_ALLOWED_ORIGIN_REGEX,
        allow_credentials=True,
        allow_private_network=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_private_network_cors_headers(request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    app.include_router(system_controller.router)
    app.include_router(auth_controller.router)
    app.include_router(users_controller.router)
    app.include_router(organizations_controller.router)
    app.include_router(members_controller.router)
    app.include_router(documents_controller.router)
    app.include_router(chat_controller.router)
    app.include_router(analytics_controller.router)
    app.include_router(settings_controller.router)
    app.include_router(billing_controller.router)
    app.include_router(notifications_controller.router)

    @app.on_event("startup")
    def startup() -> None:
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()
