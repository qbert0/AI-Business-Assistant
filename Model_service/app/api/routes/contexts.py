from fastapi import APIRouter

from app.schemas.context import ContextBuildRequest, ContextBuildResponse
from app.services.context_service import ContextService


router = APIRouter(prefix="/contexts", tags=["Contexts"])


@router.post("/build", response_model=ContextBuildResponse, summary="Assemble context cho mot query")
def build_context(payload: ContextBuildRequest) -> ContextBuildResponse:
    return ContextService().build_context(payload)
