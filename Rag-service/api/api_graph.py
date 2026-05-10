from fastapi import APIRouter, HTTPException

from services import get_graphiti_service

router = APIRouter()


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
