from fastapi.testclient import TestClient


def test_create_document(client: TestClient) -> None:
    response = client.post(
        "/search/documents",
        json={
            "index_name": "products",
            "document_id": "p-001",
            "document": {
                "name": "MacBook Pro",
                "price": 1999,
            },
            "refresh": True,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "code": "000",
        "message": "Success",
        "data": {
            "backend": "fake-elasticsearch",
            "index_name": "products",
            "document_id": "p-001",
            "document": {
                "name": "MacBook Pro",
                "price": 1999,
            },
            "result": "created",
            "version": 1,
        },
    }


def test_get_document(client: TestClient) -> None:
    client.post(
        "/search/documents",
        json={
            "index_name": "products",
            "document_id": "p-002",
            "document": {
                "name": "Mechanical Keyboard",
                "price": 129,
            },
        },
    )

    response = client.get("/search/documents/products/p-002")

    assert response.status_code == 200
    assert response.json() == {
        "code": "000",
        "message": "Success",
        "data": {
            "backend": "fake-elasticsearch",
            "index_name": "products",
            "document_id": "p-002",
            "document": {
                "name": "Mechanical Keyboard",
                "price": 129,
            },
            "result": "found",
            "version": 1,
        },
    }


def test_update_document(client: TestClient) -> None:
    client.post(
        "/search/documents",
        json={
            "index_name": "products",
            "document_id": "p-003",
            "document": {
                "name": "Monitor",
                "price": 300,
            },
        },
    )

    response = client.put(
        "/search/documents/products/p-003",
        json={
            "document": {
                "price": 279,
                "in_stock": True,
            },
            "refresh": True,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "code": "000",
        "message": "Success",
        "data": {
            "backend": "fake-elasticsearch",
            "index_name": "products",
            "document_id": "p-003",
            "document": {
                "name": "Monitor",
                "price": 279,
                "in_stock": True,
            },
            "result": "updated",
            "version": 2,
        },
    }


def test_delete_document(client: TestClient) -> None:
    client.post(
        "/search/documents",
        json={
            "index_name": "products",
            "document_id": "p-004",
            "document": {
                "name": "Mouse",
                "price": 49,
            },
        },
    )

    response = client.delete("/search/documents/products/p-004?refresh=true")

    assert response.status_code == 200
    assert response.json() == {
        "code": "000",
        "message": "Success",
        "data": {
            "backend": "fake-elasticsearch",
            "index_name": "products",
            "document_id": "p-004",
            "deleted": True,
            "result": "deleted",
        },
    }


def test_create_document_returns_conflict_when_document_exists(
    client: TestClient,
) -> None:
    payload = {
        "index_name": "products",
        "document_id": "p-005",
        "document": {
            "name": "Docking Station",
            "price": 199,
        },
    }

    first_response = client.post("/search/documents", json=payload)
    second_response = client.post("/search/documents", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Document 'p-005' already exists in index 'products'."
    }


def test_get_document_returns_not_found_for_missing_document(
    client: TestClient,
) -> None:
    response = client.get("/search/documents/products/missing-id")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Document 'missing-id' was not found in index 'products'."
    }

