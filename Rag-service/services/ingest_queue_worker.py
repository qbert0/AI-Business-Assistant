from __future__ import annotations

import asyncio
import socket
from typing import Any

from conn import QueueMessage, RedisStreamClient, ServerServiceClient
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
        self.server_service_client = ServerServiceClient()

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
                document_id = str(payload["document_id"])
                metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
                acting_user_id = str(metadata.get("acting_user_id") or "")
                logger.info(
                    "Processing rag ingest job "
                    f"message_id={message_id} "
                    f"document_id={payload.get('document_id')} "
                    f"chunk_count={len(payload.get('chunks') or [])}"
                )
                if acting_user_id:
                    if await self.server_service_client.is_cancel_requested(document_id, acting_user_id):
                        await self._patch_document(
                            document_id,
                            acting_user_id,
                            status="cancelled",
                            stage="cancelled",
                            message="Da dung truoc khi xay dung graph.",
                            analysis={
                                "state": "cancelled",
                                "locked": False,
                                "stage": "cancelled",
                                "message": "Da dung truoc khi xay dung graph.",
                                "cancel_requested": False,
                            },
                        )
                        await self.redis_client.ack(self.queue_name, self.group_name, message_id)
                        return

                    await self._patch_document(
                        document_id,
                        acting_user_id,
                        status="indexing",
                        stage="graph",
                        message="RAG service dang xay dung graph tim kiem.",
                        analysis={
                            "state": "graphing",
                            "locked": True,
                            "stage": "graph",
                            "message": "RAG service dang xay dung graph tim kiem.",
                        },
                        progress={"parse": 100, "graph": 35},
                    )

                await self.graphiti_service.ingest_chunks(
                    document_id=document_id,
                    document_name=str(payload["document_name"]),
                    source=str(payload.get("source") or "worker-service"),
                    source_description=payload.get("source_description"),
                    metadata=metadata,
                    chunks=payload["chunks"],
                )
                if acting_user_id:
                    await self._patch_document(
                        document_id,
                        acting_user_id,
                        status="indexed",
                        stage="graph",
                        message="Da hoan tat xay dung graph tim kiem.",
                        analysis={
                            "state": "indexed",
                            "locked": False,
                            "stage": "graph",
                            "message": "Da hoan tat xay dung graph tim kiem.",
                            "cancel_requested": False,
                        },
                        progress={"parse": 100, "graph": 100},
                    )
                await self.redis_client.ack(self.queue_name, self.group_name, message_id)
                logger.info(f"Completed rag ingest job message_id={message_id}")
            except Exception as exc:
                logger.exception(f"Rag ingest job failed message_id={message_id}: {exc}")
                payload = message.payload if isinstance(message.payload, dict) else {}
                metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
                document_id = payload.get("document_id")
                acting_user_id = metadata.get("acting_user_id")
                if document_id and acting_user_id:
                    await self._patch_document(
                        str(document_id),
                        str(acting_user_id),
                        status="failed",
                        stage="graph",
                        message=f"RAG service xu ly that bai: {exc}",
                        analysis={
                            "state": "failed",
                            "locked": False,
                            "stage": "graph",
                            "message": f"RAG service xu ly that bai: {exc}",
                            "error": str(exc),
                        },
                        progress={"graph": 35},
                    )
                await self.redis_client.ack(self.queue_name, self.group_name, message_id)

    async def _patch_document(
        self,
        document_id: str,
        acting_user_id: str,
        *,
        status: str,
        stage: str,
        message: str,
        analysis: dict[str, Any],
        progress: dict[str, int] | None = None,
    ) -> None:
        await self.server_service_client.update_document_status(
            document_id,
            acting_user_id,
            {
                "status": status,
                "stage": stage,
                "message": message,
                "analysis": analysis,
                "progress": progress,
            },
        )
