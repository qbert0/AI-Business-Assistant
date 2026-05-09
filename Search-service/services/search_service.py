from __future__ import annotations

from api.search_document_schema import (
    SearchDocumentCreateRequest,
    SearchDocumentDeleteRead,
    SearchDocumentQueryHitRead,
    SearchDocumentQueryRequest,
    SearchDocumentRead,
    SearchDocumentUpdateRequest,
)
from repositories.search_repository import SearchRepository


class SearchService:
    def __init__(self, repository: SearchRepository) -> None:
        self.repository = repository

    @property
    def backend_name(self) -> str:
        return self.repository.search_engine.backend_name

    def create_document(self, payload: SearchDocumentCreateRequest) -> SearchDocumentRead:
        document = self.repository.create_document(
            index_name=payload.index_name,
            document_id=payload.document_id,
            document=payload.document,
            refresh=payload.refresh,
        )
        return SearchDocumentRead.from_domain(backend=self.backend_name, document=document)

    def query_documents(self, payload: SearchDocumentQueryRequest) -> list[SearchDocumentQueryHitRead]:
        hits = self.repository.query_documents(
            index_name=payload.index_name,
            query=payload.query,
            size=payload.size,
            fields=payload.fields,
        )
        return [
            SearchDocumentQueryHitRead.from_domain(
                backend=self.backend_name,
                hit=hit,
            )
            for hit in hits
        ]

    def get_document(self, *, index_name: str, document_id: str) -> SearchDocumentRead:
        document = self.repository.get_document(index_name=index_name, document_id=document_id)
        return SearchDocumentRead.from_domain(backend=self.backend_name, document=document)

    def update_document(
        self,
        *,
        index_name: str,
        document_id: str,
        payload: SearchDocumentUpdateRequest,
    ) -> SearchDocumentRead:
        document = self.repository.update_document(
            index_name=index_name,
            document_id=document_id,
            document=payload.document,
            refresh=payload.refresh,
        )
        return SearchDocumentRead.from_domain(backend=self.backend_name, document=document)

    def delete_document(
        self,
        *,
        index_name: str,
        document_id: str,
        refresh: bool,
    ) -> SearchDocumentDeleteRead:
        result = self.repository.delete_document(
            index_name=index_name,
            document_id=document_id,
            refresh=refresh,
        )
        return SearchDocumentDeleteRead.from_domain(backend=self.backend_name, result=result)
