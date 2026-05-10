import sys
import asyncio
import argparse

from conn.redis_client import RedisStreamClient
from utils.constants import (
    WORKER_BATCH_SIZE,
    WORKER_BLOCK_MS,
    WORKER_CONCURRENT,
    WORKER_CONSUMER_NAME,
    WORKER_GROUP_NAME,
    WORKER_MAX_PENDING_RETRY,
    WORKER_QUEUE_NAME,
)
from utils.logs import logger
from worker import PayloadParserWorker, RedisQueueSupervisor


async def main(concurrent: int):
    redis_client = RedisStreamClient()
    worker = PayloadParserWorker()
    supervisor = RedisQueueSupervisor(
        redis_client=redis_client,
        worker=worker,
        queue_name=WORKER_QUEUE_NAME,
        group_name=WORKER_GROUP_NAME,
        consumer_name=WORKER_CONSUMER_NAME,
        concurrent=concurrent,
        batch_size=WORKER_BATCH_SIZE,
        block_ms=WORKER_BLOCK_MS,
        max_pending_retry=WORKER_MAX_PENDING_RETRY,
    )
    await supervisor.start()


def cli():
    parser = argparse.ArgumentParser(description="File Preprocess Executor")
    parser.add_argument(
        "--concurrent",
        type=int,
        default=WORKER_CONCURRENT,
        help="Number of concurrent tasks to maintain.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(concurrent=args.concurrent))
    except KeyboardInterrupt:
        logger.info("Executor stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    cli()
