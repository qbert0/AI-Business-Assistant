from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from api.response_schema import DataResponse
from api.search_document_schema import (
    SearchDocumentCreateRequest,
    SearchDocumentDeleteRead,
    SearchDocumentQueryHitRead,
    SearchDocumentQueryRequest,
    SearchDocumentRead,
    SearchDocumentUpdateRequest,
)
from dependencies import get_search_engine
from repositories.search_repository import SearchRepository
from search_engines.exceptions import (
    SearchDocumentAlreadyExistsError,
    SearchDocumentNotFoundError,
    SearchEngineConnectionError,
    SearchEngineError,
    UnsupportedSearchBackendError,
)
from services.search_service import SearchService

router = APIRouter()


def _get_search_service_dependency() -> SearchService:
    try:
        return SearchService(SearchRepository(get_search_engine()))
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


def _raise_operation_http_exception(exc: SearchEngineError) -> None:
    if isinstance(exc, SearchDocumentAlreadyExistsError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    if isinstance(exc, SearchDocumentNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if isinstance(exc, SearchEngineConnectionError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(exc),
    ) from exc


@router.post(
    "",
    response_model=DataResponse[SearchDocumentRead],
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    payload: SearchDocumentCreateRequest,
    search_service: SearchService = Depends(_get_search_service_dependency),
):
    try:
        document = search_service.create_document(payload)
    except SearchEngineError as exc:
        _raise_operation_http_exception(exc)

    return DataResponse[SearchDocumentRead].success_response(document)


@router.post(
    "/query",
    response_model=DataResponse[list[SearchDocumentQueryHitRead]],
)
def query_documents(
    payload: SearchDocumentQueryRequest,
    search_service: SearchService = Depends(_get_search_service_dependency),
):
    try:
        hits = search_service.query_documents(payload)
    except SearchEngineError as exc:
        _raise_operation_http_exception(exc)

    return DataResponse[list[SearchDocumentQueryHitRead]].success_response(hits)


@router.get(
    "/{index_name}/{document_id}",
    response_model=DataResponse[SearchDocumentRead],
)
def get_document(
    index_name: str,
    document_id: str,
    search_service: SearchService = Depends(_get_search_service_dependency),
):
    try:
        document = search_service.get_document(index_name=index_name, document_id=document_id)
    except SearchEngineError as exc:
        _raise_operation_http_exception(exc)

    return DataResponse[SearchDocumentRead].success_response(document)


@router.put(
    "/{index_name}/{document_id}",
    response_model=DataResponse[SearchDocumentRead],
)
def update_document(
    index_name: str,
    document_id: str,
    payload: SearchDocumentUpdateRequest,
    search_service: SearchService = Depends(_get_search_service_dependency),
):
    try:
        document = search_service.update_document(
            index_name=index_name,
            document_id=document_id,
            payload=payload,
        )
    except SearchEngineError as exc:
        _raise_operation_http_exception(exc)

    return DataResponse[SearchDocumentRead].success_response(document)


@router.delete(
    "/{index_name}/{document_id}",
    response_model=DataResponse[SearchDocumentDeleteRead],
)
def delete_document(
    index_name: str,
    document_id: str,
    refresh: bool = True,
    search_service: SearchService = Depends(_get_search_service_dependency),
):
    try:
        result = search_service.delete_document(
            index_name=index_name,
            document_id=document_id,
            refresh=refresh,
        )
    except SearchEngineError as exc:
        _raise_operation_http_exception(exc)

    return DataResponse[SearchDocumentDeleteRead].success_response(
        result
    )
