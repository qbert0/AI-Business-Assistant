from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResult:
    response_text: str
    finish_reason: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    raw_response: dict[str, Any]


@dataclass
class HealthCheckResult:
    status: str
    detail: str


class ProviderRequestError(Exception):
    """Raised when the upstream model serving endpoint cannot fulfill a request."""


class BaseLLMClient:
    def __init__(self, base_url: str, model_name: str, api_key: str | None, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResult:
        raise NotImplementedError

    def health_check(self) -> HealthCheckResult:
        raise NotImplementedError
