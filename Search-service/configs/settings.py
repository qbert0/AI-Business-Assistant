from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from utils.constants import (
    DEFAULT_SEARCH_BACKEND,
    ELASTICSEARCH_PASSWORD,
    ELASTICSEARCH_REQUEST_TIMEOUT,
    ELASTICSEARCH_URL,
    ELASTICSEARCH_USERNAME,
    ELASTICSEARCH_VERIFY_CERTS,
)


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
        backend=DEFAULT_SEARCH_BACKEND,
        elasticsearch_url=ELASTICSEARCH_URL,
        elasticsearch_username=ELASTICSEARCH_USERNAME,
        elasticsearch_password=ELASTICSEARCH_PASSWORD,
        elasticsearch_verify_certs=ELASTICSEARCH_VERIFY_CERTS,
        elasticsearch_request_timeout=ELASTICSEARCH_REQUEST_TIMEOUT,
    )
