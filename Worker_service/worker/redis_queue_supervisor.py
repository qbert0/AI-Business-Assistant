import asyncio
import os
import socket
from typing import Optional

from conn.redis_client import Message, RedisStreamClient
from utils.logs import logger
from worker.payload_parser_worker import PayloadParserWorker


class RedisQueueSupervisor:
    def __init__(
        self,
        redis_client: RedisStreamClient,
        worker: PayloadParserWorker,
        queue_name: str,
        group_name: str,
        consumer_name: Optional[str] = None,
        concurrent: int = 33,
        batch_size: int = 20,
        block_ms: int = 5000,
        max_pending_retry: int = 100,
    ) -> None:
        self.redis_client = redis_client
        self.worker = worker
        self.queue_name = queue_name
        self.group_name = group_name
        self.consumer_name = consumer_name or self._default_consumer_name()
        self.concurrent = max(1, concurrent)
        self.batch_size = max(1, batch_size)
        self.block_ms = max(100, block_ms)
        self.max_pending_retry = max(0, max_pending_retry)

        self.shutdown_event = asyncio.Event()
        self.message_queue: asyncio.Queue[Message] = asyncio.Queue(maxsize=self.concurrent)
        self.runner_tasks: list[asyncio.Task] = []
        self.reader_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self.redis_client.connect()

        is_healthy = await self.redis_client.health()
        if not is_healthy:
            raise RuntimeError("Redis is not healthy")

        await self.redis_client.create_group(self.queue_name, self.group_name)
        await self._recover_pending_messages()

        logger.info(
            "Starting Redis queue supervisor "
            f"queue={self.queue_name} group={self.group_name} consumer={self.consumer_name} concurrent={self.concurrent}"
        )

        self.reader_task = asyncio.create_task(self._reader_loop(), name="redis-reader")
        self.runner_tasks = [
            asyncio.create_task(self._runner_loop(index), name=f"worker-runner-{index}")
            for index in range(self.concurrent)
        ]

        try:
            await asyncio.gather(*self.runner_tasks)
        finally:
            await self.stop()

    async def stop(self) -> None:
        if self.shutdown_event.is_set():
            return

        self.shutdown_event.set()

        if self.reader_task is not None:
            self.reader_task.cancel()
            await asyncio.gather(self.reader_task, return_exceptions=True)
            self.reader_task = None

        if self.runner_tasks:
            for task in self.runner_tasks:
                task.cancel()
            await asyncio.gather(*self.runner_tasks, return_exceptions=True)
            self.runner_tasks.clear()

        await self.redis_client.close()
        logger.info("Redis queue supervisor stopped")

    async def _reader_loop(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                available_slots = self.message_queue.maxsize - self.message_queue.qsize()
                if available_slots <= 0:
                    await asyncio.sleep(0.05)
                    continue

                fetch_count = min(self.batch_size, available_slots)
                messages = await self.redis_client.consume(
                    queue_name=self.queue_name,
                    group_name=self.group_name,
                    consumer_name=self.consumer_name,
                    count=fetch_count,
                    block=self.block_ms,
                )

                if not messages:
                    continue

                for message in messages:
                    await self.message_queue.put(message)

                logger.info(
                    f"Buffered {len(messages)} messages, queue_fill={self.message_queue.qsize()}/{self.message_queue.maxsize}"
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(f"Reader loop error: {exc}")
                await asyncio.sleep(1)

    async def _runner_loop(self, index: int) -> None:
        runner_name = f"{self.consumer_name}-slot-{index + 1}"
        logger.info(f"Runner started: {runner_name}")

        while not self.shutdown_event.is_set():
            try:
                message = await self.message_queue.get()
            except asyncio.CancelledError:
                raise

            try:
                await self.worker.handle(message)
                if message.id:
                    await self.redis_client.ack(self.queue_name, self.group_name, message.id)
                logger.info(f"Runner {runner_name} completed message_id={message.id}")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(
                    f"Runner {runner_name} failed message_id={message.id}: {exc}"
                )
            finally:
                self.message_queue.task_done()

    async def _recover_pending_messages(self) -> None:
        if self.max_pending_retry <= 0:
            return

        try:
            recovered_messages = await self.redis_client.claim_pending(
                queue_name=self.queue_name,
                group_name=self.group_name,
                consumer_name=self.consumer_name,
                count=min(self.concurrent, self.max_pending_retry),
                min_idle_ms=0,
            )

            for message in recovered_messages:
                if self.message_queue.full():
                    break
                await self.message_queue.put(message)

            if recovered_messages:
                logger.info(
                    f"Recovered {len(recovered_messages)} pending messages into local queue"
                )
        except Exception as exc:
            logger.warning(f"Pending recovery skipped: {exc}")

    @staticmethod
    def _default_consumer_name() -> str:
        host = socket.gethostname()
        pid = os.getpid()
        return f"{host}-{pid}"
