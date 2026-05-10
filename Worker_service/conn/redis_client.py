import json
from dataclasses import dataclass, field
from typing import Any, Optional

from redis.asyncio import Redis

from utils.constants import REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from utils.logs import logger


@dataclass(slots=True)
class Message:
    payload: dict[str, Any]
    id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class RedisStreamClient:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
    ) -> None:
        self.host = host or REDIS_HOST
        self.port = int(port if port is not None else REDIS_PORT)
        self.db = int(db if db is not None else REDIS_DB)
        self.password = password if password is not None else REDIS_PASSWORD
        self.client: Optional[Redis] = None

    def connect(self) -> None:
        try:
            self.client = Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,
            )
        except Exception as exc:
            logger.error(f"Failed to connect to Redis: {exc}")
            raise ValueError(f"Failed to connect to Redis: {exc}") from exc

    async def close(self) -> None:
        if self.client is not None:
            await self.client.aclose()
            self.client = None

    async def health(self) -> bool:
        client = self._require_client()
        try:
            return bool(await client.ping())
        except Exception as exc:
            logger.error(f"Failed to ping Redis: {exc}")
            return False

    async def publish(self, queue_name: str, message: Message) -> str:
        client = self._require_client()
        try:
            body = json.dumps(
                {
                    "payload": message.payload,
                    "metadata": message.metadata,
                    "queue_name": queue_name,
                }
            )
            redis_id = await client.xadd(queue_name, {"message": body})
            message.id = self._decode_value(redis_id)
            logger.info(f"Published message {message.id} to queue {queue_name}")
            return message.id
        except Exception as exc:
            logger.error(f"Failed to publish message to queue {queue_name}: {exc}")
            raise ValueError(f"Failed to publish message to queue {queue_name}: {exc}") from exc

    async def group_exists(self, queue_name: str, group_name: str) -> bool:
        client = self._require_client()
        try:
            groups = await client.xinfo_groups(queue_name)
            return any(self._decode_value(group.get("name", b"")) == group_name for group in groups)
        except Exception:
            return False

    async def create_group(self, queue_name: str, group_name: str, start_id: str = "0") -> None:
        client = self._require_client()
        try:
            await client.xgroup_create(queue_name, group_name, id=start_id, mkstream=True)
            logger.info(f"Created consumer group '{group_name}' for queue '{queue_name}'")
        except Exception as exc:
            if "BUSYGROUP" in str(exc):
                logger.warning(
                    f"Consumer group '{group_name}' already exists for queue '{queue_name}'"
                )
                return
            logger.error(
                f"Failed to create consumer group '{group_name}' for queue '{queue_name}': {exc}"
            )
            raise ValueError(
                f"Failed to create consumer group '{group_name}' for queue '{queue_name}': {exc}"
            ) from exc

    async def consume(
        self,
        queue_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        block: int = 5000,
    ) -> list[Message]:
        client = self._require_client()
        try:
            if not await self.group_exists(queue_name, group_name):
                await self.create_group(queue_name, group_name)

            response = await client.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={queue_name: ">"},
                count=count,
                block=block,
            )
            messages = self._parse_stream_response(response)
            logger.debug(
                f"Consumer '{consumer_name}' consumed {len(messages)} messages from queue '{queue_name}'"
            )
            return messages
        except Exception as exc:
            logger.error(
                f"Failed to consume from queue '{queue_name}' (group: {group_name}, consumer: {consumer_name}): {exc}"
            )
            raise ValueError(
                f"Failed to consume from queue '{queue_name}' (group: {group_name}, consumer: {consumer_name}): {exc}"
            ) from exc

    async def ack(self, queue_name: str, group_name: str, message_id: str) -> None:
        client = self._require_client()
        try:
            await client.xack(queue_name, group_name, message_id)
            logger.debug(f"Acked message {message_id}")
        except Exception as exc:
            logger.error(f"Failed to ack message {message_id}: {exc}")
            raise ValueError(f"Failed to ack message {message_id}: {exc}") from exc

    async def list_pending(
        self,
        queue_name: str,
        group_name: str,
        count: int = 10,
    ) -> list[Message]:
        client = self._require_client()
        try:
            pending_entries = await client.xpending_range(
                queue_name,
                group_name,
                min="-",
                max="+",
                count=count,
            )
            messages: list[Message] = []
            for entry in pending_entries:
                message_id = self._decode_value(entry["message_id"])
                result = await client.xrange(queue_name, min=message_id, max=message_id)
                if not result:
                    continue
                _, fields = result[0]
                parsed = self._parse_message_fields(message_id, fields)
                if parsed is not None:
                    messages.append(parsed)
            return messages
        except Exception as exc:
            logger.error(f"Failed to list pending messages: {exc}")
            raise ValueError(f"Failed to list pending messages: {exc}") from exc

    async def claim_pending(
        self,
        queue_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        min_idle_ms: int = 0,
    ) -> list[Message]:
        client = self._require_client()
        try:
            result = await client.xautoclaim(
                queue_name,
                group_name,
                consumer_name,
                min_idle_time=min_idle_ms,
                start_id="0-0",
                count=count,
            )
            if not result or len(result) < 2:
                return []

            claimed_messages = result[1]
            messages: list[Message] = []
            for message_id, fields in claimed_messages:
                parsed = self._parse_message_fields(self._decode_value(message_id), fields)
                if parsed is not None:
                    messages.append(parsed)
            return messages
        except Exception as exc:
            logger.error(f"Failed to claim pending messages: {exc}")
            raise ValueError(f"Failed to claim pending messages: {exc}") from exc

    def _parse_stream_response(self, response: list[Any]) -> list[Message]:
        messages: list[Message] = []
        for _, stream_messages in response or []:
            for message_id, fields in stream_messages:
                parsed = self._parse_message_fields(self._decode_value(message_id), fields)
                if parsed is not None:
                    messages.append(parsed)
        return messages

    def _parse_message_fields(self, message_id: str, fields: dict[Any, Any]) -> Optional[Message]:
        raw_message = fields.get(b"message") or fields.get("message") or b"{}"
        try:
            message_data = json.loads(self._decode_value(raw_message))
            payload = message_data.get("payload", {})
            metadata = message_data.get("metadata", {})
            return Message(id=message_id, payload=payload, metadata=metadata)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error(f"Failed to parse message {message_id}: {exc}")
            return None

    def _require_client(self) -> Redis:
        if self.client is None:
            self.connect()
        if self.client is None:
            raise ValueError("Redis client is not initialized")
        return self.client

    @staticmethod
    def _decode_value(value: Any) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)
