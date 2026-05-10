from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from redis.asyncio import Redis

from utils.constants import REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from utils.logs import logger


@dataclass
class QueueMessage:
    payload: dict[str, Any]
    id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class RedisStreamClient:
    def __init__(
        self,
        *,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB,
        password: str | None = REDIS_PASSWORD,
    ) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client: Redis | None = None

    def connect(self) -> None:
        self.client = Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
        )

    async def close(self) -> None:
        if self.client is not None:
            await self.client.aclose()
            self.client = None

    async def publish(self, queue_name: str, message: QueueMessage) -> str:
        client = self._require_client()
        body = json.dumps(
            {
                "payload": message.payload,
                "metadata": message.metadata,
            },
            ensure_ascii=False,
        )
        redis_id = await client.xadd(queue_name, {"message": body})
        message_id = redis_id.decode() if isinstance(redis_id, bytes) else str(redis_id)
        logger.info(f"Published ingest job queue={queue_name} message_id={message_id}")
        return message_id

    async def create_group(self, queue_name: str, group_name: str) -> None:
        client = self._require_client()
        try:
            await client.xgroup_create(queue_name, group_name, id="0", mkstream=True)
            logger.info(f"Created Redis consumer group queue={queue_name} group={group_name}")
        except Exception as exc:
            if "BUSYGROUP" in str(exc):
                logger.warning(f"Redis consumer group already exists queue={queue_name} group={group_name}")
                return
            raise

    async def consume(
        self,
        *,
        queue_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 5000,
    ) -> list[QueueMessage]:
        client = self._require_client()
        response = await client.xreadgroup(
            groupname=group_name,
            consumername=consumer_name,
            streams={queue_name: ">"},
            count=count,
            block=block_ms,
        )
        return self._parse_stream_response(response)

    async def ack(self, queue_name: str, group_name: str, message_id: str) -> None:
        client = self._require_client()
        await client.xack(queue_name, group_name, message_id)

    def _parse_stream_response(self, response: list[Any]) -> list[QueueMessage]:
        messages: list[QueueMessage] = []
        for _, stream_messages in response or []:
            for message_id, fields in stream_messages:
                raw_message = fields.get(b"message") or fields.get("message")
                if not raw_message:
                    continue
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode("utf-8")
                payload = json.loads(raw_message)
                payload_body = payload.get("payload")
                metadata = payload.get("metadata", {})
                if not isinstance(payload_body, dict):
                    continue
                parsed_id = message_id.decode("utf-8") if isinstance(message_id, bytes) else str(message_id)
                messages.append(
                    QueueMessage(
                        id=parsed_id,
                        payload=payload_body,
                        metadata=metadata if isinstance(metadata, dict) else {},
                    )
                )
        return messages

    def _require_client(self) -> Redis:
        if self.client is None:
            raise ValueError("Redis client is not connected")
        return self.client
