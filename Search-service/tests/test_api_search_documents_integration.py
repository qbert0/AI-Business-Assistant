from __future__ import annotations

import os
import time
import uuid
from typing import Iterator

import httpx
import pytest


def _wait_for_search_service(
    client: httpx.Client,
    base_url: str,
    timeout_seconds: int = 60,
) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            response = client.get("/health")
            if response.status_code == 200:
                payload = response.json()
                if payload.get("data", {}).get("backend_available") is True:
                    return
        except Exception as exc:  # pragma: no cover - network-dependent
            last_error = exc
        time.sleep(1)

    message = (
        f"Search-service is not reachable at {base_url}.\n"
        "Start it first with:\n"
        "docker compose -f Search-service/docker-compose.yml up -d --build search-service"
    )
    if last_error is not None:
        message = f"{message}\nLast error: {last_error}"
    pytest.fail(message)


@pytest.fixture
def search_service_base_url() -> str:
    return os.getenv("SEARCH_SERVICE_BASE_URL", "http://127.0.0.1:8001")


@pytest.fixture
def integration_client(
    search_service_base_url: str,
) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=search_service_base_url, timeout=30.0) as client:
        _wait_for_search_service(client, search_service_base_url)
        yield client


@pytest.fixture
def test_index() -> str:
    return f"search-service-it-{uuid.uuid4().hex}"


@pytest.fixture
def created_documents(
    integration_client: httpx.Client,
    test_index: str,
) -> Iterator[list[str]]:
    document_ids: list[str] = []
    yield document_ids

    for document_id in document_ids:
        integration_client.delete(f"/search/documents/{test_index}/{document_id}?refresh=true")


def _create_document(
    client: httpx.Client,
    *,
    index_name: str,
    document_id: str,
    document: dict,
):
    response = client.post(
        "/search/documents",
        json={
            "index_name": index_name,
            "document_id": document_id,
            "document": document,
            "refresh": True,
        },
    )
    assert response.status_code == 201, response.text
    return response


def test_healthcheck_with_real_search_service(
    integration_client: httpx.Client,
) -> None:
    response = integration_client.get("/health")

    assert response.status_code == 200, response.text
    assert response.json()["data"]["backend"] == "elasticsearch"
    assert response.json()["data"]["backend_available"] is True


def test_create_document_through_real_api(
    integration_client: httpx.Client,
    test_index: str,
    created_documents: list[str],
) -> None:
    response = _create_document(
        integration_client,
        index_name=test_index,
        document_id="doc-create",
        document={"title": "Create test", "views": 10},
    )
    created_documents.append("doc-create")

    assert response.json()["data"] == {
        "backend": "elasticsearch",
        "index_name": test_index,
        "document_id": "doc-create",
        "document": {"title": "Create test", "views": 10},
        "result": "created",
        "version": 1,
    }


def test_get_document_through_real_api(
    integration_client: httpx.Client,
    test_index: str,
    created_documents: list[str],
) -> None:
    _create_document(
        integration_client,
        index_name=test_index,
        document_id="doc-read",
        document={"title": "Read test", "views": 20},
    )
    created_documents.append("doc-read")

    response = integration_client.get(f"/search/documents/{test_index}/doc-read")

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {
        "backend": "elasticsearch",
        "index_name": test_index,
        "document_id": "doc-read",
        "document": {"title": "Read test", "views": 20},
        "result": "found",
        "version": 1,
    }


def test_update_document_through_real_api(
    integration_client: httpx.Client,
    test_index: str,
    created_documents: list[str],
) -> None:
    _create_document(
        integration_client,
        index_name=test_index,
        document_id="doc-update",
        document={"title": "Before update", "views": 1},
    )
    created_documents.append("doc-update")

    response = integration_client.put(
        f"/search/documents/{test_index}/doc-update",
        json={
            "document": {"title": "After update", "published": True},
            "refresh": True,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {
        "backend": "elasticsearch",
        "index_name": test_index,
        "document_id": "doc-update",
        "document": {
            "title": "After update",
            "views": 1,
            "published": True,
        },
        "result": "updated",
        "version": 2,
    }


def test_delete_document_through_real_api(
    integration_client: httpx.Client,
    test_index: str,
) -> None:
    _create_document(
        integration_client,
        index_name=test_index,
        document_id="doc-delete",
        document={"title": "Delete test"},
    )

    response = integration_client.delete(
        f"/search/documents/{test_index}/doc-delete?refresh=true"
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {
        "backend": "elasticsearch",
        "index_name": test_index,
        "document_id": "doc-delete",
        "deleted": True,
        "result": "deleted",
    }

    missing_response = integration_client.get(
        f"/search/documents/{test_index}/doc-delete"
    )
    assert missing_response.status_code == 404, missing_response.text


def test_create_document_conflict_through_real_api(
    integration_client: httpx.Client,
    test_index: str,
    created_documents: list[str],
) -> None:
    _create_document(
        integration_client,
        index_name=test_index,
        document_id="doc-conflict",
        document={"title": "Conflict test"},
    )
    created_documents.append("doc-conflict")

    response = integration_client.post(
        "/search/documents",
        json={
            "index_name": test_index,
            "document_id": "doc-conflict",
            "document": {"title": "Conflict again"},
            "refresh": True,
        },
    )

    assert response.status_code == 409, response.text
    assert response.json() == {
        "detail": f"Document 'doc-conflict' already exists in index '{test_index}'."
    }


def test_get_missing_document_through_real_api(
    integration_client: httpx.Client,
    test_index: str,
) -> None:
    response = integration_client.get(f"/search/documents/{test_index}/missing-doc")

    assert response.status_code == 404, response.text
    assert response.json() == {
        "detail": f"Document 'missing-doc' was not found in index '{test_index}'."
    }
