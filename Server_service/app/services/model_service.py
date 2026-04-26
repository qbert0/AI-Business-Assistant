import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app import messages
from app.config import MODEL_SERVICE_TIMEOUT, MODEL_SERVICE_URL


def create_inference(payload: dict) -> dict:
    request = Request(
        f"{MODEL_SERVICE_URL}/api/v1/inferences",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=MODEL_SERVICE_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{messages.MODEL_SERVICE_UNAVAILABLE}: {detail or exc.reason}",
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=messages.MODEL_SERVICE_UNAVAILABLE,
        ) from exc
