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
            f"Server-service config must be a YAML object: '{CONFIG_FILE_PATH}'."
        )

    return payload


CONFIG = _load_config()
OAUTH_CONFIG = CONFIG.get("oauth", {}) if isinstance(CONFIG, dict) else {}
GOOGLE_OAUTH_CONFIG = OAUTH_CONFIG.get("google", {}) if isinstance(OAUTH_CONFIG, dict) else {}

if not isinstance(GOOGLE_OAUTH_CONFIG, dict):
    raise ValueError(
        f"Server-service config section 'oauth.google' must be a YAML object: '{CONFIG_FILE_PATH}'."
    )

GOOGLE_OAUTH_CLIENT_ID = str(GOOGLE_OAUTH_CONFIG.get("client_id", "")).strip()
GOOGLE_OAUTH_CLIENT_SECRET = str(GOOGLE_OAUTH_CONFIG.get("client_secret", "")).strip()
