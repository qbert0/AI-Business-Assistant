from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from api.api_router import router
from constants import API_PREFIX

def get_application() -> FastAPI:
    application = FastAPI(
        title="AI Business Assistant Search Service",
        docs_url="/docs",
        redoc_url="/re-docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
        description="""
        AI Business Assistant Search Service
        """,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    application.include_router(router, prefix=API_PREFIX)

    return application

app = get_application()