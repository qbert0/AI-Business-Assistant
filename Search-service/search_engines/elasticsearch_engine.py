from __future__ import annotations

from importlib import import_module
from typing import Any, Mapping

from search_engines.base import (
    AbstractSearchEngine,
    SearchDeleteResult,
    SearchDocument,
    SearchQueryHit,
)
from search_engines.exceptions import (
    SearchDocumentAlreadyExistsError,
    SearchDocumentNotFoundError,
    SearchEngineConnectionError,
    SearchEngineError,
)


class ElasticsearchSearchEngine(AbstractSearchEngine):
    def __init__(
        self,
        *,
        url: str,
        username: str | None = None,
        password: str | None = None,
        verify_certs: bool = False,
        request_timeout: int = 30,
    ) -> None:
        elasticsearch_module = self._load_elasticsearch_module()

        self._api_error = getattr(elasticsearch_module, "ApiError", Exception)
        self._conflict_error = getattr(
            elasticsearch_module, "ConflictError", self._api_error
        )
        self._not_found_error = getattr(
            elasticsearch_module, "NotFoundError", self._api_error
        )
        self._transport_error = getattr(
            elasticsearch_module, "TransportError", Exception
        )

        client_kwargs: dict[str, Any] = {
            "hosts": [url],
            "verify_certs": verify_certs,
            "request_timeout": request_timeout,
        }
        if username and password:
            client_kwargs["basic_auth"] = (username, password)

        self._client = elasticsearch_module.Elasticsearch(**client_kwargs)

    @property
    def backend_name(self) -> str:
        return "elasticsearch"

    def ping(self) -> bool:
        try:
            return bool(self._client.ping())
        except self._transport_error as exc:
            raise SearchEngineConnectionError(
                "Cannot connect to Elasticsearch."
            ) from exc
        except Exception as exc:
            raise SearchEngineConnectionError(
                "Unexpected error while pinging Elasticsearch."
            ) from exc

    def create_document(
        self,
        index_name: str,
        document_id: str,
        document: Mapping[str, Any],
        *,
        refresh: bool = True,
    ) -> SearchDocument:
        try:
            response = self._client.create(
                index=index_name,
                id=document_id,
                document=dict(document),
                refresh=self._refresh_value(refresh),
            )
            return self._build_document(
                response=response,
                document=document,
                fallback_index=index_name,
                fallback_document_id=document_id,
            )
        except self._conflict_error as exc:
            raise SearchDocumentAlreadyExistsError(
                f"Document '{document_id}' already exists in index '{index_name}'."
            ) from exc
        except self._api_error as exc:
            raise SearchEngineError(
                f"Elasticsearch create operation failed for index '{index_name}'."
            ) from exc
        except Exception as exc:
            raise SearchEngineConnectionError(
                "Unexpected error while creating document in Elasticsearch."
            ) from exc

    def get_document(self, index_name: str, document_id: str) -> SearchDocument:
        try:
            response = self._client.get(index=index_name, id=document_id)
            normalized_response = dict(response)
            if normalized_response.get("found") is True:
                normalized_response.setdefault("result", "found")
            return self._build_document(
                response=normalized_response,
                fallback_index=index_name,
                fallback_document_id=document_id,
            )
        except self._not_found_error as exc:
            raise SearchDocumentNotFoundError(
                f"Document '{document_id}' was not found in index '{index_name}'."
            ) from exc
        except self._api_error as exc:
            raise SearchEngineError(
                f"Elasticsearch read operation failed for index '{index_name}'."
            ) from exc
        except Exception as exc:
            raise SearchEngineConnectionError(
                "Unexpected error while reading document from Elasticsearch."
            ) from exc

    def update_document(
        self,
        index_name: str,
        document_id: str,
        document: Mapping[str, Any],
        *,
        refresh: bool = True,
    ) -> SearchDocument:
        try:
            response = self._client.update(
                index=index_name,
                id=document_id,
                doc=dict(document),
                refresh=self._refresh_value(refresh),
                source=True,
            )
            current_document = self._extract_document(response)
            if current_document is None:
                fetched_document = self.get_document(index_name, document_id)
                fetched_document.result = response.get("result")
                fetched_document.version = response.get(
                    "_version", fetched_document.version
                )
                return fetched_document

            return self._build_document(
                response=response,
                document=current_document,
                fallback_index=index_name,
                fallback_document_id=document_id,
            )
        except self._not_found_error as exc:
            raise SearchDocumentNotFoundError(
                f"Document '{document_id}' was not found in index '{index_name}'."
            ) from exc
        except self._api_error as exc:
            raise SearchEngineError(
                f"Elasticsearch update operation failed for index '{index_name}'."
            ) from exc
        except Exception as exc:
            raise SearchEngineConnectionError(
                "Unexpected error while updating document in Elasticsearch."
            ) from exc

    def delete_document(
        self,
        index_name: str,
        document_id: str,
        *,
        refresh: bool = True,
    ) -> SearchDeleteResult:
        try:
            response = self._client.delete(
                index=index_name,
                id=document_id,
                refresh=self._refresh_value(refresh),
            )
            return SearchDeleteResult(
                index_name=response.get("_index", index_name),
                document_id=response.get("_id", document_id),
                deleted=response.get("result") == "deleted",
                result=response.get("result"),
            )
        except self._not_found_error as exc:
            raise SearchDocumentNotFoundError(
                f"Document '{document_id}' was not found in index '{index_name}'."
            ) from exc
        except self._api_error as exc:
            raise SearchEngineError(
                f"Elasticsearch delete operation failed for index '{index_name}'."
            ) from exc
        except Exception as exc:
            raise SearchEngineConnectionError(
                "Unexpected error while deleting document from Elasticsearch."
            ) from exc

    def query_documents(
        self,
        index_name: str,
        query: str,
        *,
        size: int = 10,
        fields: list[str] | None = None,
    ) -> list[SearchQueryHit]:
        try:
            search_fields = fields or ["file_name^3", "content", "text", "metadata.*"]
            response = self._client.search(
                index=index_name,
                size=size,
                query={
                    "multi_match": {
                        "query": query,
                        "fields": search_fields,
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                        "lenient": True,
                    }
                },
            )
            hits = response.get("hits", {}).get("hits", [])
            return [
                SearchQueryHit(
                    index_name=hit.get("_index", index_name),
                    document_id=hit.get("_id", ""),
                    score=hit.get("_score"),
                    document=dict(hit.get("_source") or {}),
                )
                for hit in hits
            ]
        except self._not_found_error:
            return []
        except self._api_error as exc:
            raise SearchEngineError(
                f"Elasticsearch query operation failed for index '{index_name}'."
            ) from exc
        except Exception as exc:
            raise SearchEngineConnectionError(
                "Unexpected error while querying Elasticsearch."
            ) from exc

    @staticmethod
    def _load_elasticsearch_module():
        try:
            return import_module("elasticsearch")
        except ImportError as exc:
            raise SearchEngineError(
                "Missing dependency 'elasticsearch'. Install Search-service/requirements.txt."
            ) from exc

    @staticmethod
    def _refresh_value(refresh: bool) -> str | bool:
        return "wait_for" if refresh else False

    @staticmethod
    def _extract_document(response: Mapping[str, Any]) -> dict[str, Any] | None:
        if "_source" in response:
            return dict(response["_source"])

        inner_get = response.get("get")
        if isinstance(inner_get, Mapping) and "_source" in inner_get:
            return dict(inner_get["_source"])

        return None

    def _build_document(
        self,
        *,
        response: Mapping[str, Any],
        fallback_index: str,
        fallback_document_id: str,
        document: Mapping[str, Any] | None = None,
    ) -> SearchDocument:
        current_document = (
            dict(document)
            if document is not None
            else self._extract_document(response) or {}
        )
        return SearchDocument(
            index_name=response.get("_index", fallback_index),
            document_id=response.get("_id", fallback_document_id),
            document=current_document,
            result=response.get("result"),
            version=response.get("_version"),
        )
