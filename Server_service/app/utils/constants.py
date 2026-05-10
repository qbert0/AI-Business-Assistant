from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT_PATH = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_PATH / "configs"
CONFIG_FILE_PATH = CONFIG_PATH / "config.yml"
CONFIG_EXAMPLE_FILE_PATH = CONFIG_PATH / "config.example.yml"


def _resolve_config_file_path() -> Path:
    if CONFIG_FILE_PATH.exists():
        return CONFIG_FILE_PATH
    if CONFIG_EXAMPLE_FILE_PATH.exists():
        return CONFIG_EXAMPLE_FILE_PATH
    raise FileNotFoundError(
        "Server-service config file was not found. Expected one of: "
        f"'{CONFIG_FILE_PATH}' or '{CONFIG_EXAMPLE_FILE_PATH}'."
    )


def _load_config() -> dict[str, Any]:
    resolved_config_file_path = _resolve_config_file_path()

    with resolved_config_file_path.open("r", encoding="utf-8") as config_file:
        payload = yaml.safe_load(config_file) or {}

    if not isinstance(payload, dict):
        raise ValueError(
            "Server-service config must be a YAML object: "
            f"'{resolved_config_file_path}'."
        )

    return payload


CONFIG = _load_config()
OAUTH_CONFIG = CONFIG.get("oauth", {}) if isinstance(CONFIG, dict) else {}
GOOGLE_OAUTH_CONFIG = OAUTH_CONFIG.get("google", {}) if isinstance(OAUTH_CONFIG, dict) else {}

if not isinstance(GOOGLE_OAUTH_CONFIG, dict):
    raise ValueError(
        "Server-service config section 'oauth.google' must be a YAML object: "
        f"'{_resolve_config_file_path()}'."
    )

GOOGLE_OAUTH_CLIENT_ID = str(GOOGLE_OAUTH_CONFIG.get("client_id", "")).strip()
GOOGLE_OAUTH_CLIENT_SECRET = str(GOOGLE_OAUTH_CONFIG.get("client_secret", "")).strip()
