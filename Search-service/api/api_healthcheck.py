from fastapi import APIRouter, Depends, HTTPException, status

from api.health_schema import SearchBackendHealthRead
from api.response_schema import DataResponse
from dependencies import get_search_engine
from search_engines.base import AbstractSearchEngine
from search_engines.exceptions import SearchEngineError, UnsupportedSearchBackendError

router = APIRouter()


def _get_search_engine_dependency() -> AbstractSearchEngine:
    try:
        return get_search_engine()
    except UnsupportedSearchBackendError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except SearchEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("", response_model=DataResponse[SearchBackendHealthRead])
async def get(
    search_engine: AbstractSearchEngine = Depends(_get_search_engine_dependency),
):
    try:
        backend_available = search_engine.ping()
    except SearchEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return DataResponse[SearchBackendHealthRead].success_response(
        SearchBackendHealthRead(
            backend=search_engine.backend_name,
            backend_available=backend_available,
        )
    )
