from fastapi import APIRouter

from conn import ModelServiceClient, Neo4jClient

router = APIRouter()

neo4j_client = Neo4jClient()
model_service_client = ModelServiceClient()


@router.get("")
async def get() -> dict[str, object]:
    return {
        "status": "ok",
        "neo4j": {
            "uri": neo4j_client.uri,
            "healthy": neo4j_client.health(),
        },
        "model_service": {
            "base_url": model_service_client.base_url,
            "healthy": await model_service_client.health(),
        },
    }
