from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT_PATH = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_PATH / "configs"
CONFIG_FILE_PATH = CONFIG_PATH / "config.yml"


def _load_config() -> dict[str, Any]:
    with CONFIG_FILE_PATH.open("r", encoding="utf-8") as config_file:
        payload = yaml.safe_load(config_file) or {}

    if not isinstance(payload, dict):
        raise ValueError(
            f"Search-service config must be a YAML object: '{CONFIG_FILE_PATH}'."
        )

    return payload


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalize_route(path: str, default: str) -> str:
    normalized = (path or default).strip()
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized.rstrip("/") or "/"


CONFIG = _load_config()
APP_CONFIG = _as_dict(CONFIG.get("app"))
ROUTES_CONFIG = _as_dict(APP_CONFIG.get("routes"))
SEARCH_CONFIG = _as_dict(CONFIG.get("search"))
ELASTICSEARCH_CONFIG = _as_dict(SEARCH_CONFIG.get("elasticsearch"))

API_PREFIX = (str(APP_CONFIG.get("api_prefix", "")) or "").rstrip("/")

DEFAULT_SEARCH_BACKEND = (
    str(SEARCH_CONFIG.get("backend", "elasticsearch")).strip().lower()
    or "elasticsearch"
)

HEALTH_ROUTE_PREFIX = _normalize_route(
    str(ROUTES_CONFIG.get("health", "/health")),
    "/health",
)
SEARCH_DOCUMENTS_ROUTE_PREFIX = _normalize_route(
    str(ROUTES_CONFIG.get("search_documents", "/search/documents")),
    "/search/documents",
)

ELASTICSEARCH_URL = str(
    ELASTICSEARCH_CONFIG.get("url", "http://localhost:9200")
).strip()
ELASTICSEARCH_USERNAME = (
    str(ELASTICSEARCH_CONFIG["username"]).strip()
    if ELASTICSEARCH_CONFIG.get("username") is not None
    else None
)
ELASTICSEARCH_PASSWORD = (
    str(ELASTICSEARCH_CONFIG["password"]).strip()
    if ELASTICSEARCH_CONFIG.get("password") is not None
    else None
)
ELASTICSEARCH_VERIFY_CERTS = bool(
    ELASTICSEARCH_CONFIG.get("verify_certs", False)
)
ELASTICSEARCH_REQUEST_TIMEOUT = int(
    ELASTICSEARCH_CONFIG.get("request_timeout", 30)
)
