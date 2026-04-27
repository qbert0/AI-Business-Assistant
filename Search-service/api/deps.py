from __future__ import annotations

from functools import lru_cache

from configs import get_settings
from search_engines.base import AbstractSearchEngine
from search_engines.factory import SearchEngineFactory


@lru_cache(maxsize=1)
def get_search_engine() -> AbstractSearchEngine:
    return SearchEngineFactory.create(get_settings())
