from dataclasses import dataclass

from app.infrastructure.llm.base import LLMResult


@dataclass(frozen=True)
class InferenceResultEntity:
    request: object
    response: object
    context: object


@dataclass(frozen=True)
class ProviderHealthEntity:
    model_id: str
    status: str
    detail: str
    checked_at: object


@dataclass(frozen=True)
class UpstreamInferenceEntity:
    model: object
    result: LLMResult
