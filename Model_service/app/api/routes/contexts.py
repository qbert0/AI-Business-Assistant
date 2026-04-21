from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.context import ContextBuildRequest, ContextBuildResponse, StoredContextDetail, StoredContextRead
from app.services.context_service import ContextService


router = APIRouter(prefix="/contexts", tags=["Contexts"])


@router.post("/build", response_model=ContextBuildResponse, summary="Assemble context cho mot query")
def build_context(payload: ContextBuildRequest) -> ContextBuildResponse:
    return ContextService().build_context(payload)


@router.get("", response_model=list[StoredContextRead], summary="Lay danh sach context da luu")
def list_contexts(
    conversation_id: str | None = Query(None),
    organization_id: str | None = Query(None),
    user_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[StoredContextRead]:
    return ContextService().list_stored_contexts(
        db,
        conversation_id=conversation_id,
        organization_id=organization_id,
        user_id=user_id,
        limit=limit,
    )


@router.get("/{request_id}", response_model=StoredContextDetail, summary="Lay context da luu theo request")
def get_context(request_id: str, db: Session = Depends(get_db)) -> StoredContextDetail:
    return ContextService().get_stored_context(db, request_id)
