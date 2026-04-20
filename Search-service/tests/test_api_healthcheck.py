from fastapi.testclient import TestClient


def test_healthcheck_returns_backend_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": "000",
        "message": "Success",
        "data": {
            "backend": "fake-elasticsearch",
            "backend_available": True,
        },
    }
