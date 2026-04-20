from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

SEARCH_SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(SEARCH_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SEARCH_SERVICE_DIR))

from api import api_healthcheck, api_search_documents  # noqa: E402
from main import app  # noqa: E402
from search_engines.base import (  # noqa: E402
    AbstractSearchEngine,
    SearchDeleteResult,
    SearchDocument,
)
from search_engines.exceptions import (  # noqa: E402
    SearchDocumentAlreadyExistsError,
    SearchDocumentNotFoundError,
)


class FakeSearchEngine(AbstractSearchEngine):
    def __init__(self) -> None:
        self._documents: dict[tuple[str, str], dict] = {}
        self._versions: dict[tuple[str, str], int] = {}
        self._backend_available = True

    @property
    def backend_name(self) -> str:
        return "fake-elasticsearch"

    def ping(self) -> bool:
        return self._backend_available

    def create_document(
        self,
        index_name: str,
        document_id: str,
        document: dict,
        *,
        refresh: bool = True,
    ) -> SearchDocument:
        key = (index_name, document_id)
        if key in self._documents:
            raise SearchDocumentAlreadyExistsError(
                f"Document '{document_id}' already exists in index '{index_name}'."
            )

        self._documents[key] = dict(document)
        self._versions[key] = 1
        return SearchDocument(
            index_name=index_name,
            document_id=document_id,
            document=dict(document),
            result="created",
            version=self._versions[key],
        )

    def get_document(self, index_name: str, document_id: str) -> SearchDocument:
        key = (index_name, document_id)
        if key not in self._documents:
            raise SearchDocumentNotFoundError(
                f"Document '{document_id}' was not found in index '{index_name}'."
            )

        return SearchDocument(
            index_name=index_name,
            document_id=document_id,
            document=dict(self._documents[key]),
            result="found",
            version=self._versions[key],
        )

    def update_document(
        self,
        index_name: str,
        document_id: str,
        document: dict,
        *,
        refresh: bool = True,
    ) -> SearchDocument:
        key = (index_name, document_id)
        if key not in self._documents:
            raise SearchDocumentNotFoundError(
                f"Document '{document_id}' was not found in index '{index_name}'."
            )

        self._documents[key].update(document)
        self._versions[key] += 1
        return SearchDocument(
            index_name=index_name,
            document_id=document_id,
            document=dict(self._documents[key]),
            result="updated",
            version=self._versions[key],
        )

    def delete_document(
        self,
        index_name: str,
        document_id: str,
        *,
        refresh: bool = True,
    ) -> SearchDeleteResult:
        key = (index_name, document_id)
        if key not in self._documents:
            raise SearchDocumentNotFoundError(
                f"Document '{document_id}' was not found in index '{index_name}'."
            )

        del self._documents[key]
        del self._versions[key]
        return SearchDeleteResult(
            index_name=index_name,
            document_id=document_id,
            deleted=True,
            result="deleted",
        )


@pytest.fixture
def fake_search_engine() -> FakeSearchEngine:
    return FakeSearchEngine()


@pytest.fixture
def client(fake_search_engine: FakeSearchEngine) -> Iterator[TestClient]:
    app.dependency_overrides[api_healthcheck._get_search_engine_dependency] = (
        lambda: fake_search_engine
    )
    app.dependency_overrides[api_search_documents._get_search_engine_dependency] = (
        lambda: fake_search_engine
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
