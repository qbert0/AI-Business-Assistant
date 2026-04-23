from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from constants import DEFAULT_SEARCH_BACKEND


def _get_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class SearchSettings:
    backend: str
    elasticsearch_url: str
    elasticsearch_username: str | None
    elasticsearch_password: str | None
    elasticsearch_verify_certs: bool
    elasticsearch_request_timeout: int


@lru_cache(maxsize=1)
def get_settings() -> SearchSettings:
    return SearchSettings(
        backend=os.getenv("SEARCH_ENGINE_BACKEND", DEFAULT_SEARCH_BACKEND).strip().lower(),
        elasticsearch_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200").strip(),
        elasticsearch_username=_get_optional_env("ELASTICSEARCH_USERNAME"),
        elasticsearch_password=_get_optional_env("ELASTICSEARCH_PASSWORD"),
        elasticsearch_verify_certs=_get_bool_env("ELASTICSEARCH_VERIFY_CERTS", False),
        elasticsearch_request_timeout=_get_int_env("ELASTICSEARCH_REQUEST_TIMEOUT", 30),
    )
