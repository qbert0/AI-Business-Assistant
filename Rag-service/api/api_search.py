from fastapi import APIRouter, HTTPException

from api.search_schema import SearchFactsRequest, SearchNodesRequest
from services import get_graphiti_service

router = APIRouter()


@router.post("/nodes")
async def search_nodes(payload: SearchNodesRequest) -> dict[str, object]:
    try:
        graphiti_service = await get_graphiti_service()
        results = await graphiti_service.search_nodes(
            query=payload.query,
            limit=payload.limit,
            group_id=payload.group_id,
        )
        return {
            "status": "ok",
            "results": results,
            "count": len(results),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Node search failed",
                "error": str(exc),
            },
        ) from exc


@router.post("/facts")
async def search_facts(payload: SearchFactsRequest) -> dict[str, object]:
    try:
        graphiti_service = await get_graphiti_service()
        results = await graphiti_service.search_facts(
            query=payload.query,
            limit=payload.limit,
            center_node_uuid=payload.center_node_uuid,
            group_id=payload.group_id,
        )
        return {
            "status": "ok",
            "results": results,
            "count": len(results),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Fact search failed",
                "error": str(exc),
            },
        ) from exc
