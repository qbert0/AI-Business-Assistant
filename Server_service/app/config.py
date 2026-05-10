import os
from dataclasses import dataclass

from app.utils.constants import CONFIG


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT", "").rstrip("/")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "business-documents")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_PRESIGN_EXPIRES_SECONDS = max(300, int(os.getenv("MINIO_PRESIGN_EXPIRES_SECONDS", "86400")))
STORAGE_PUBLIC_ENDPOINT = os.getenv("STORAGE_PUBLIC_ENDPOINT", "").rstrip("/")
SERVER_INTERNAL_URL = os.getenv("SERVER_INTERNAL_URL", "http://server_service:8000").rstrip("/")

WORKER_REDIS_HOST = os.getenv("WORKER_REDIS_HOST", "redis")
WORKER_REDIS_PORT = int(os.getenv("WORKER_REDIS_PORT", "6379"))
WORKER_REDIS_DB = int(os.getenv("WORKER_REDIS_DB", "0"))
WORKER_REDIS_PASSWORD = os.getenv("WORKER_REDIS_PASSWORD") or None
WORKER_QUEUE_NAME = os.getenv("WORKER_QUEUE_NAME", "file-preprocess")

SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8000").rstrip("/")
SEARCH_SERVICE_TIMEOUT = int(os.getenv("SEARCH_SERVICE_TIMEOUT", "10"))
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model_service:8888").rstrip("/")
MODEL_SERVICE_TIMEOUT = int(os.getenv("MODEL_SERVICE_TIMEOUT", "90"))

CORS_ALLOWED_ORIGIN_REGEX = os.getenv("CORS_ALLOWED_ORIGIN_REGEX", ".*")
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_SENDER = os.getenv("SMTP_SENDER", SMTP_USERNAME or "noreply@business-assistant.local").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() != "false"


def _config_section(name: str) -> dict:
    value = CONFIG.get(name, {}) if isinstance(CONFIG, dict) else {}
    return value if isinstance(value, dict) else {}


def _nested_int(section: dict, path: list[str], default: int, minimum: int = 1) -> int:
    current = section
    for key in path[:-1]:
        if not isinstance(current, dict):
            return default
        current = current.get(key, {})
    if not isinstance(current, dict):
        return default

    raw_value = current.get(path[-1], default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return max(minimum, value)


AGENT_CONFIG_SECTION = _config_section("agent")


@dataclass(frozen=True)
class PlannerAgentSettings:
    history_limit: int


@dataclass(frozen=True)
class SearchQuestionAgentSettings:
    history_limit: int


@dataclass(frozen=True)
class RetrievalAgentSettings:
    no_hit_retries: int
    max_queries_per_attempt: int
    hits_per_query: int
    max_merged_hits: int
    max_context_items: int
    context_char_limit: int


@dataclass(frozen=True)
class AnswererAgentSettings:
    max_completion_tokens: int
    compact_context_items: int
    compact_context_chars: int


@dataclass(frozen=True)
class VerifierAgentSettings:
    max_completion_tokens: int
    max_context_chars_for_model_verify: int


@dataclass(frozen=True)
class FeedbackAgentSettings:
    history_limit: int
    comment_char_limit: int
    answer_char_limit: int


@dataclass(frozen=True)
class SynthesizerAgentSettings:
    max_completion_tokens: int
    context_item_limit: int
    context_char_limit: int


@dataclass(frozen=True)
class AgentSettings:
    planner: PlannerAgentSettings
    questioner: SearchQuestionAgentSettings
    retrieval: RetrievalAgentSettings
    answerer: AnswererAgentSettings
    verifier: VerifierAgentSettings
    feedback: FeedbackAgentSettings
    synthesizer: SynthesizerAgentSettings


AGENT_SETTINGS = AgentSettings(
    planner=PlannerAgentSettings(
        history_limit=_nested_int(AGENT_CONFIG_SECTION, ["planner", "history_limit"], 16),
    ),
    questioner=SearchQuestionAgentSettings(
        history_limit=_nested_int(AGENT_CONFIG_SECTION, ["questioner", "history_limit"], 16),
    ),
    retrieval=RetrievalAgentSettings(
        no_hit_retries=_nested_int(AGENT_CONFIG_SECTION, ["retrieval", "no_hit_retries"], 2, minimum=0),
        max_queries_per_attempt=_nested_int(AGENT_CONFIG_SECTION, ["retrieval", "max_queries_per_attempt"], 4),
        hits_per_query=_nested_int(AGENT_CONFIG_SECTION, ["retrieval", "hits_per_query"], 8),
        max_merged_hits=_nested_int(AGENT_CONFIG_SECTION, ["retrieval", "max_merged_hits"], 24),
        max_context_items=_nested_int(AGENT_CONFIG_SECTION, ["retrieval", "max_context_items"], 8),
        context_char_limit=_nested_int(AGENT_CONFIG_SECTION, ["retrieval", "context_char_limit"], 5000),
    ),
    answerer=AnswererAgentSettings(
        max_completion_tokens=_nested_int(AGENT_CONFIG_SECTION, ["answerer", "max_completion_tokens"], 6000),
        compact_context_items=_nested_int(AGENT_CONFIG_SECTION, ["answerer", "compact_context_items"], 8),
        compact_context_chars=_nested_int(AGENT_CONFIG_SECTION, ["answerer", "compact_context_chars"], 3000),
    ),
    verifier=VerifierAgentSettings(
        max_completion_tokens=_nested_int(AGENT_CONFIG_SECTION, ["verifier", "max_completion_tokens"], 5000),
        max_context_chars_for_model_verify=_nested_int(
            AGENT_CONFIG_SECTION,
            ["verifier", "max_context_chars_for_model_verify"],
            24000,
        ),
    ),
    feedback=FeedbackAgentSettings(
        history_limit=_nested_int(AGENT_CONFIG_SECTION, ["feedback", "history_limit"], 8),
        comment_char_limit=_nested_int(AGENT_CONFIG_SECTION, ["feedback", "comment_char_limit"], 400),
        answer_char_limit=_nested_int(AGENT_CONFIG_SECTION, ["feedback", "answer_char_limit"], 600),
    ),
    synthesizer=SynthesizerAgentSettings(
        max_completion_tokens=_nested_int(AGENT_CONFIG_SECTION, ["synthesizer", "max_completion_tokens"], 6000),
        context_item_limit=_nested_int(AGENT_CONFIG_SECTION, ["synthesizer", "context_item_limit"], 8),
        context_char_limit=_nested_int(AGENT_CONFIG_SECTION, ["synthesizer", "context_char_limit"], 3000),
    ),
)
