import json
from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException, status

from app import messages
from app.config import WORKER_QUEUE_NAME, WORKER_REDIS_DB, WORKER_REDIS_HOST, WORKER_REDIS_PASSWORD, WORKER_REDIS_PORT

try:
    from redis import Redis
except ImportError:  # pragma: no cover
    Redis = None


@dataclass(slots=True)
class WorkerMessage:
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


def publish_document_analysis_job(payload: dict[str, Any]) -> str:
    if Redis is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis client chua duoc cai dat cho Server_service.",
        )

    try:
        client = Redis(
            host=WORKER_REDIS_HOST,
            port=WORKER_REDIS_PORT,
            db=WORKER_REDIS_DB,
            password=WORKER_REDIS_PASSWORD,
            decode_responses=True,
        )
        message = WorkerMessage(
            payload=payload,
            metadata={"source": "server-service", "job_type": "document-analysis"},
        )
        body = json.dumps(
            {
                "payload": message.payload,
                "metadata": message.metadata,
                "queue_name": WORKER_QUEUE_NAME,
            }
        )
        message_id = client.xadd(WORKER_QUEUE_NAME, {"message": body})
        return str(message_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{messages.DOCUMENT_INGEST_ACCEPTED} Redis publish failed: {exc}",
        ) from exc
