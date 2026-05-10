from __future__ import annotations

import asyncio
import socket
from typing import Any

from conn import QueueMessage, RedisStreamClient
from utils.constants import (
    INGEST_BATCH_SIZE,
    INGEST_BLOCK_MS,
    INGEST_CONCURRENT,
    INGEST_CONSUMER_NAME,
    INGEST_GROUP_NAME,
    INGEST_QUEUE_NAME,
)
from utils.logs import logger


class IngestQueueWorker:
    def __init__(
        self,
        *,
        redis_client: RedisStreamClient,
        graphiti_service,
        queue_name: str = INGEST_QUEUE_NAME,
        group_name: str = INGEST_GROUP_NAME,
        consumer_name: str | None = INGEST_CONSUMER_NAME,
        concurrent: int = INGEST_CONCURRENT,
        batch_size: int = INGEST_BATCH_SIZE,
        block_ms: int = INGEST_BLOCK_MS,
    ) -> None:
        self.redis_client = redis_client
        self.graphiti_service = graphiti_service
        self.queue_name = queue_name
        self.group_name = group_name
        self.consumer_name = consumer_name or f"{socket.gethostname()}-rag-ingest"
        self.concurrent = max(1, concurrent)
        self.batch_size = max(1, batch_size)
        self.block_ms = max(100, block_ms)
        self._reader_task: asyncio.Task | None = None
        self._active_tasks: set[asyncio.Task] = set()
        self._stopping = False
        self._semaphore = asyncio.Semaphore(self.concurrent)

    async def start(self) -> None:
        self.redis_client.connect()
        await self.redis_client.create_group(self.queue_name, self.group_name)
        self._stopping = False
        self._reader_task = asyncio.create_task(self._reader_loop())
        logger.info(
            "Started rag ingest queue worker "
            f"queue={self.queue_name} group={self.group_name} consumer={self.consumer_name} "
            f"concurrent={self.concurrent}"
        )

    async def stop(self) -> None:
        self._stopping = True
        if self._reader_task is not None:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
            self._active_tasks.clear()

        await self.redis_client.close()
        logger.info("Stopped rag ingest queue worker")

    async def _reader_loop(self) -> None:
        while not self._stopping:
            try:
                messages = await self.redis_client.consume(
                    queue_name=self.queue_name,
                    group_name=self.group_name,
                    consumer_name=self.consumer_name,
                    count=self.batch_size,
                    block_ms=self.block_ms,
                )
                for message in messages:
                    task = asyncio.create_task(self._handle_message(message))
                    self._active_tasks.add(task)
                    task.add_done_callback(self._active_tasks.discard)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception(f"Rag ingest queue reader failed: {exc}")
                await asyncio.sleep(1.0)

    async def _handle_message(self, message: QueueMessage) -> None:
        async with self._semaphore:
            message_id = message.id or "unknown"
            try:
                payload = message.payload
                logger.info(
                    "Processing rag ingest job "
                    f"message_id={message_id} "
                    f"document_id={payload.get('document_id')} "
                    f"chunk_count={len(payload.get('chunks') or [])}"
                )
                await self.graphiti_service.ingest_chunks(
                    document_id=str(payload["document_id"]),
                    document_name=str(payload["document_name"]),
                    source=str(payload.get("source") or "worker-service"),
                    source_description=payload.get("source_description"),
                    metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
                    chunks=payload["chunks"],
                )
                await self.redis_client.ack(self.queue_name, self.group_name, message_id)
                logger.info(f"Completed rag ingest job message_id={message_id}")
            except Exception as exc:
                logger.exception(f"Rag ingest job failed message_id={message_id}: {exc}")
