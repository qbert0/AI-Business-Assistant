import asyncio
import sys

from conn import RedisStreamClient
from services import IngestQueueWorker, get_graphiti_service
from utils.logs import logger


async def main() -> None:
    graphiti_service = await get_graphiti_service()
    redis_client = RedisStreamClient()
    worker = IngestQueueWorker(
        redis_client=redis_client,
        graphiti_service=graphiti_service,
    )
    await worker.start()

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await worker.stop()


def cli() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("RAG worker stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    cli()
