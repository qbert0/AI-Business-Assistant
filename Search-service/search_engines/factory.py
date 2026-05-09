from __future__ import annotations

from configs import SearchSettings
from search_engines.base import AbstractSearchEngine
from search_engines.elasticsearch_engine import ElasticsearchSearchEngine
from search_engines.exceptions import UnsupportedSearchBackendError


class SearchEngineFactory:
    @staticmethod
    def create(settings: SearchSettings) -> AbstractSearchEngine:
        if settings.backend == "elasticsearch":
            return ElasticsearchSearchEngine(
                url=settings.elasticsearch_url,
                username=settings.elasticsearch_username,
                password=settings.elasticsearch_password,
                verify_certs=settings.elasticsearch_verify_certs,
                request_timeout=settings.elasticsearch_request_timeout,
            )

        raise UnsupportedSearchBackendError(
            f"Unsupported search backend '{settings.backend}'."
        )
