import argparse
import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from conn.redis_client import Message, RedisStreamClient
from utils.constants import WORKER_QUEUE_NAME
from utils.logs import logger


def build_default_payload() -> dict:
    sample_filename = "6-thang-dau-nam-tp-hcm-da-trien-khai-131-cuoc-thanh-tra-hanh-chinh.txt"
    return {
        "task_id": str(uuid4()),
        "task_type": "local-parse-test",
        "filename": sample_filename,
        "local_path": sample_filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "content": {"source": "local-file"},
    }


async def main(queue_name: str, payload_raw: str | None) -> None:
    redis_client = RedisStreamClient()
    redis_client.connect()

    try:
        payload = json.loads(payload_raw) if payload_raw else build_default_payload()
        message = Message(
            payload=payload,
            metadata={
                "source": "publish_test_task",
                "queue_name": queue_name,
            },
        )
        message_id = await redis_client.publish(queue_name, message)
        logger.info(f"Published test task to queue={queue_name} message_id={message_id}")
        print(message_id)
    finally:
        await redis_client.close()


def cli() -> None:
    parser = argparse.ArgumentParser(description="Publish a test task to Redis stream.")
    parser.add_argument(
        "--queue",
        default=WORKER_QUEUE_NAME,
        help="Redis stream queue name.",
    )
    parser.add_argument(
        "--payload",
        default=None,
        help="Optional JSON payload string. If omitted, a default payload is used.",
    )
    args = parser.parse_args()

    asyncio.run(main(queue_name=args.queue, payload_raw=args.payload))


if __name__ == "__main__":
    cli()
