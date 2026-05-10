from __future__ import annotations

from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing PyYAML. Install with: pip install -r scripts/requirements.txt") from exc
    content = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(content, dict):
        raise RuntimeError(f"Config must be a YAML object: {config_path}")
    return content


def get_nested(config: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = config
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
