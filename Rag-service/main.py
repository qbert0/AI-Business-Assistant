import argparse

import uvicorn
from fastapi import FastAPI
from api.api_ingest import redis_client as ingest_queue_client
from api.api_healthcheck import neo4j_client
from api.api_router import router as api_router
from utils.constants import APP_HOST, APP_PORT

app = FastAPI(
    title="RAG Service",
    version="0.1.0",
    description="Service for graph ingestion, indexing, and retrieval.",
)
app.include_router(api_router)


@app.on_event("startup")
async def startup_event() -> None:
    neo4j_client.connect()
    ingest_queue_client.connect()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await ingest_queue_client.close()
    neo4j_client.close()


def cli() -> None:
    parser = argparse.ArgumentParser(description="RAG Service")
    parser.add_argument("--host", default=APP_HOST)
    parser.add_argument("--port", type=int, default=APP_PORT)
    args = parser.parse_args()

    uvicorn.run("main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    cli()
