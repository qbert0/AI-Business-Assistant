from __future__ import annotations

from search_engines.base import AbstractSearchEngine


class SearchRepository:
    def __init__(self, search_engine: AbstractSearchEngine) -> None:
        self.search_engine = search_engine

    def create_document(
        self,
        *,
        index_name: str,
        document_id: str,
        document: dict,
        refresh: bool,
    ):
        return self.search_engine.create_document(
            index_name=index_name,
            document_id=document_id,
            document=document,
            refresh=refresh,
        )

    def query_documents(
        self,
        *,
        index_name: str,
        query: str,
        size: int,
        fields: list[str] | None,
    ):
        return self.search_engine.query_documents(
            index_name=index_name,
            query=query,
            size=size,
            fields=fields,
        )

    def get_document(self, *, index_name: str, document_id: str):
        return self.search_engine.get_document(index_name=index_name, document_id=document_id)

    def update_document(
        self,
        *,
        index_name: str,
        document_id: str,
        document: dict,
        refresh: bool,
    ):
        return self.search_engine.update_document(
            index_name=index_name,
            document_id=document_id,
            document=document,
            refresh=refresh,
        )

    def delete_document(self, *, index_name: str, document_id: str, refresh: bool):
        return self.search_engine.delete_document(
            index_name=index_name,
            document_id=document_id,
            refresh=refresh,
        )
