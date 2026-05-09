from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from app import models
from app.controllers import embeddings_controller, inferences_controller
from app.main import app


class _DummySession:
    def close(self) -> None:
        return None


class FakeEmbeddingService:
    @classmethod
    def from_dependencies(cls, db, settings):
        return cls()

    def create_embedding(self, payload: models.EmbeddingCreate) -> models.EmbeddingResultRead:
        assert payload.input == ["hello embedding"]
        return models.EmbeddingResultRead(
            model_id="embedding-model-id",
            model_name=payload.model or "default-embedding",
            provider_type="openai_compatible",
            dimensions=3,
            data=[models.EmbeddingVectorRead(index=0, embedding=[0.1, 0.2, 0.3])],
            usage=models.EmbeddingUsageRead(prompt_tokens=2, total_tokens=2),
        )


class FakeInferenceService:
    @classmethod
    def from_dependencies(cls, db, settings):
        return cls()

    def create_inference(self, payload: models.InferenceCreate) -> models.InferenceResult:
        assert payload.question == "Reply with exactly: test ok"
        return models.InferenceResult(
            request=models.InferenceRequestRead(
                id="request-id",
                conversation_id=payload.conversation_id,
                organization_id=payload.organization_id,
                user_id=payload.user_id,
                model_id="llm-model-id",
                policy_id=None,
                question=payload.question,
                status="completed",
                latency_ms=123,
                error_message=None,
                started_at=datetime(2026, 5, 9, 12, 0, 0),
                finished_at=datetime(2026, 5, 9, 12, 0, 1),
            ),
            response=models.InferenceResponseRead(
                id="response-id",
                request_id="request-id",
                response_text="test ok",
                finish_reason="stop",
                prompt_tokens=10,
                completion_tokens=2,
                total_tokens=12,
                estimated_cost=0.0,
                created_at=datetime(2026, 5, 9, 12, 0, 1),
            ),
            context=models.ContextBuildResponse(
                system_prompt="system",
                messages=[
                    models.ConversationMessage(role="system", content="system"),
                    models.ConversationMessage(role="user", content=payload.question),
                ],
                context_items=[],
                token_estimate=5,
            ),
        )


def test_embeddings_endpoint_returns_embedding_payload(monkeypatch) -> None:
    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.SessionLocal", lambda: _DummySession())
    monkeypatch.setattr("app.main.RegistryRepository.sync_models_from_config", lambda self: None)
    monkeypatch.setattr(embeddings_controller, "EmbeddingService", FakeEmbeddingService)

    with TestClient(app) as client:
        response = client.post("/api/v1/embeddings", json={"input": ["hello embedding"]})

    assert response.status_code == 200
    body = response.json()
    assert body["model_id"] == "embedding-model-id"
    assert body["model_name"] == "default-embedding"
    assert body["dimensions"] == 3
    assert body["data"][0]["embedding"] == [0.1, 0.2, 0.3]


def test_inferences_endpoint_returns_inference_payload(monkeypatch) -> None:
    monkeypatch.setattr("app.main.init_db", lambda: None)
    monkeypatch.setattr("app.main.SessionLocal", lambda: _DummySession())
    monkeypatch.setattr("app.main.RegistryRepository.sync_models_from_config", lambda self: None)
    monkeypatch.setattr(inferences_controller, "InferenceService", FakeInferenceService)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/inferences",
            json={
                "question": "Reply with exactly: test ok",
                "history": [],
                "external_contexts": [],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["request"]["model_id"] == "llm-model-id"
    assert body["response"]["response_text"] == "test ok"
    assert body["context"]["messages"][-1]["content"] == "Reply with exactly: test ok"
