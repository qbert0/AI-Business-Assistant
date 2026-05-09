from dataclasses import dataclass
from typing import Any


@dataclass
class EmbeddingVector:
    index: int
    embedding: list[float]


@dataclass
class EmbeddingResult:
    vectors: list[EmbeddingVector]
    prompt_tokens: int
    total_tokens: int
    raw_response: dict[str, Any]


class ProviderRequestError(Exception):
    """Raised when the upstream embedding endpoint cannot fulfill a request."""


class BaseEmbeddingClient:
    def __init__(self, base_url: str, model_name: str, api_key: str | None, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def embed(
        self,
        inputs: list[str],
        *,
        dimensions: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EmbeddingResult:
        raise NotImplementedError


__all__ = [
    "BaseEmbeddingClient",
    "EmbeddingResult",
    "EmbeddingVector",
    "ProviderRequestError",
]
