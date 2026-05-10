from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import get_graphiti_service

router = APIRouter()


class DocumentsGraphRequest(BaseModel):
    document_ids: list[str] = Field(default_factory=list)
    scope_id: str = "documents"
    limit: int = 160


@router.get("/stats")
async def get_graph_stats() -> dict[str, object]:
    try:
        graphiti_service = await get_graphiti_service()
        stats = await graphiti_service.get_graph_stats()
        return {
            "status": "ok",
            "stats": stats,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Graph stats failed",
                "error": str(exc),
            },
        ) from exc


@router.post("/documents")
async def get_documents_graph(payload: DocumentsGraphRequest) -> dict[str, object]:
    try:
        graphiti_service = await get_graphiti_service()
        graph = await graphiti_service.get_documents_graph(
            payload.document_ids,
            scope_id=payload.scope_id,
            limit=payload.limit,
        )
        return {
            "status": "ok",
            "graph": graph,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Documents graph query failed",
                "error": str(exc),
            },
        ) from exc


@router.get("/documents/{document_id}")
async def get_document_graph(document_id: str, limit: int = 80) -> dict[str, object]:
    try:
        graphiti_service = await get_graphiti_service()
        graph = await graphiti_service.get_document_graph(document_id, limit=limit)
        return {
            "status": "ok",
            "graph": graph,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Document graph query failed",
                "error": str(exc),
            },
        ) from exc
