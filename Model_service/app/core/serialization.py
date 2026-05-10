import json
from typing import Any


def parse_json_list(raw: Any) -> list[Any]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return value if isinstance(value, list) else []


def parse_json_dict(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return value if isinstance(value, dict) else {}


def dump_json(value: Any) -> str:
    # Store JSON safely even when the backing MariaDB/table collation is not
    # configured for full Unicode text. Escaping non-ASCII keeps round-tripping
    # correct while avoiding insert failures in trace/audit columns.
    return json.dumps(value if value is not None else {}, ensure_ascii=True)
