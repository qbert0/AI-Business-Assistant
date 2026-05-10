from __future__ import annotations

import time
from typing import Any


def post_json(
    base_url: str,
    path: str,
    payload: dict[str, Any],
    *,
    timeout: float,
    retries: int,
    retry_statuses: set[int] | None = None,
) -> dict[str, Any]:
    try:
        import httpx  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing httpx. Install with: pip install -r scripts/requirements.txt") from exc

    retry_statuses = retry_statuses or {502, 503, 504}
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = httpx.post(url, json=payload, timeout=timeout)
            if response.status_code in retry_statuses and attempt < retries:
                time.sleep(min(2**attempt, 8))
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
                continue
            break
    raise RuntimeError(f"POST {url} failed: {last_error}") from last_error
