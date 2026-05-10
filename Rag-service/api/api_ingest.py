from fastapi import APIRouter, HTTPException

from api.ingest_schema import IngestChunksRequest
from conn import QueueMessage, RedisStreamClient
from utils.constants import INGEST_QUEUE_NAME
from utils.logs import logger

router = APIRouter()
redis_client = RedisStreamClient()


@router.post("/chunks", status_code=202)
async def ingest_chunks(payload: IngestChunksRequest) -> dict[str, object]:
    try:
        logger.info(
            "Received chunk ingest request "
            f"document_id={payload.document_id} document_name={payload.document_name!r} "
            f"chunk_count={len(payload.chunks)} source={payload.source}"
        )
        message = QueueMessage(
            payload={
                "document_id": payload.document_id,
                "document_name": payload.document_name,
                "source": payload.source,
                "source_description": payload.source_description,
                "metadata": payload.metadata,
                "chunks": [chunk.model_dump() for chunk in payload.chunks],
            },
            metadata={
                "source": "rag-service-api",
            },
        )
        message_id = await redis_client.publish(INGEST_QUEUE_NAME, message)
        return {
            "status": "accepted",
            "message_id": message_id,
            "document_id": payload.document_id,
            "chunk_count": len(payload.chunks),
        }
    except Exception as exc:
        logger.exception(
            "Chunk ingest failed "
            f"document_id={payload.document_id} document_name={payload.document_name!r}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Graphiti chunk ingest failed",
                "error": str(exc),
            },
        ) from exc
