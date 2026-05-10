from app.db import models as db_models
from app.infrastructure.llm.base import BaseLLMClient
from app.infrastructure.llm.ollama import OllamaClient
from app.infrastructure.llm.openai_compatible import OpenAICompatibleClient


def build_llm_client(
    model: db_models.RegisteredModel,
    api_key: str | None,
    timeout_seconds: int,
    stream_response: bool = False,
) -> BaseLLMClient:
    provider_type = model.provider.provider_type
    if provider_type == "openai_compatible":
        return OpenAICompatibleClient(model.base_url, model.model_name, api_key, timeout_seconds, stream_response)
    if provider_type == "ollama":
        return OllamaClient(model.base_url, model.model_name, api_key, timeout_seconds)
    raise ValueError(f"Unsupported provider type: {provider_type}")
