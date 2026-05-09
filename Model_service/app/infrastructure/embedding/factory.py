from app.db import models as db_models
from app.infrastructure.embedding.base import BaseEmbeddingClient
from app.infrastructure.embedding.openai_compatible import OpenAICompatibleEmbeddingClient


def build_embedding_client(
    model: db_models.RegisteredModel,
    api_key: str | None,
    timeout_seconds: int,
) -> BaseEmbeddingClient:
    provider_type = model.provider.provider_type
    if provider_type == "openai_compatible":
        return OpenAICompatibleEmbeddingClient(model.base_url, model.model_name, api_key, timeout_seconds)
    raise ValueError(f"Unsupported embedding provider type: {provider_type}")
