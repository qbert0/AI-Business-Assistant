from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.configs.runtime_catalog import RuntimeModelCatalog, RuntimeModelEntry
from app.core.config import Settings
from app.core.serialization import parse_json_dict
from app.db.base import Base
from app.db import models as db_models
from app.repositories.registry_repository import RegistryRepository


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def test_sync_models_from_config_updates_and_deactivates_removed_models(monkeypatch) -> None:
    db = _make_session()
    settings = Settings(database_url="sqlite:///:memory:", model_service_secret_key="unit-test-secret")
    repository = RegistryRepository(db, settings)

    first_catalog = RuntimeModelCatalog(
        default_llm_model="gpt-oss-20b",
        default_embedding_model="text-embedding-3-small",
        llm_models=[
            RuntimeModelEntry(
                key="openai/gpt-oss-20b",
                provider_type="openai_compatible",
                model_name="gpt-oss-20b",
                base_url="http://llm-v1.example/v1",
                api_key="llm-key-v1",
                capabilities=["chat"],
                parameters={"temperature": 0, "max_tokens": 2048, "config_managed": True},
                is_default=True,
            )
        ],
        embedding_models=[
            RuntimeModelEntry(
                key="text-embedding-3-small",
                provider_type="openai_compatible",
                model_name="text-embedding-3-small",
                base_url="http://embed-v1.example/v1",
                api_key="embed-key-v1",
                capabilities=["embedding"],
                parameters={"dimensions": 1536, "config_managed": True},
                is_default=True,
            )
        ],
    )
    second_catalog = RuntimeModelCatalog(
        default_llm_model="gpt-oss-20b",
        default_embedding_model=None,
        llm_models=[
            RuntimeModelEntry(
                key="openai/gpt-oss-20b",
                provider_type="openai_compatible",
                model_name="gpt-oss-20b",
                base_url="http://llm-v2.example/v1",
                api_key="llm-key-v2",
                capabilities=["chat"],
                parameters={"temperature": 0.2, "max_tokens": 4096, "config_managed": True},
                is_default=True,
            )
        ],
        embedding_models=[],
    )

    monkeypatch.setattr("app.repositories.registry_repository.load_runtime_model_catalog", lambda: first_catalog)
    repository.sync_models_from_config()

    default_chat = repository.resolve_runtime_model(model_id=None, model_name=None, kind="chat")
    default_embedding = repository.resolve_runtime_model(model_id=None, model_name=None, kind="embedding")

    assert default_chat.base_url == "http://llm-v1.example/v1"
    assert default_embedding.base_url == "http://embed-v1.example/v1"

    monkeypatch.setattr("app.repositories.registry_repository.load_runtime_model_catalog", lambda: second_catalog)
    repository.sync_models_from_config()

    updated_chat = repository.resolve_runtime_model(model_id=None, model_name=None, kind="chat")
    removed_embedding = db.query(db_models.RegisteredModel).filter(
        db_models.RegisteredModel.display_name == "text-embedding-3-small"
    ).first()

    assert updated_chat.base_url == "http://llm-v2.example/v1"
    assert parse_json_dict(updated_chat.parameters_json)["max_tokens"] == 4096
    assert removed_embedding is not None
    assert removed_embedding.is_active is False


def test_resolve_runtime_model_returns_404_for_unknown_model(monkeypatch) -> None:
    db = _make_session()
    settings = Settings(database_url="sqlite:///:memory:", model_service_secret_key="unit-test-secret")
    repository = RegistryRepository(db, settings)
    monkeypatch.setattr(
        "app.repositories.registry_repository.load_runtime_model_catalog",
        lambda: RuntimeModelCatalog(default_llm_model=None, default_embedding_model=None),
    )

    try:
        repository.resolve_runtime_model(model_id=None, model_name="missing-model", kind="chat")
    except HTTPException as exc:
        assert exc.status_code == 404
        assert "missing-model" in exc.detail
    else:
        raise AssertionError("Expected HTTPException for missing config-managed model")
