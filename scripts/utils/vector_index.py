from __future__ import annotations

from typing import Any, Iterable

from scripts.utils.benchmark_pdf import TextChunk
from scripts.utils.http_client import post_json


def batched(items: list[Any], batch_size: int) -> Iterable[list[Any]]:
    for index in range(0, len(items), batch_size):
        yield items[index : index + batch_size]


def create_embeddings(
    chunks: list[TextChunk],
    *,
    model_service_url: str,
    organization_id: str,
    model_id: str | None,
    use_case: str,
    dimensions: int | None,
    batch_size: int,
    timeout: float,
    retries: int,
) -> tuple[list[list[float]], int]:
    vectors: list[list[float]] = []
    for batch_index, batch in enumerate(batched(chunks, batch_size), start=1):
        result = post_json(
            model_service_url,
            "/api/v1/embeddings",
            {
                "organization_id": organization_id,
                "model_id": model_id,
                "use_case": use_case,
                "input": [chunk.content for chunk in batch],
                "dimensions": dimensions,
                "metadata": {"source": "benchmark-cli", "batch_index": batch_index},
            },
            timeout=timeout,
            retries=retries,
        )
        batch_vectors = [item["embedding"] for item in sorted(result.get("data", []), key=lambda item: item["index"])]
        if len(batch_vectors) != len(batch):
            raise RuntimeError(f"Embedding count mismatch: expected={len(batch)} actual={len(batch_vectors)}")
        vectors.extend(batch_vectors)
        print(f"embedded batch {batch_index}: vectors={len(batch_vectors)}")
    if not vectors:
        raise RuntimeError("No embeddings created.")
    return vectors, len(vectors[0])


def index_elasticsearch(
    chunks: list[TextChunk],
    vectors: list[list[float]],
    *,
    url: str,
    username: str | None,
    password: str | None,
    verify_certs: bool,
    index_name: str,
    batch_size: int,
    recreate: bool,
) -> None:
    try:
        from elasticsearch import Elasticsearch, helpers  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing elasticsearch. Install with: pip install -r scripts/requirements.txt") from exc

    client_kwargs: dict[str, Any] = {
        "hosts": [url],
        "verify_certs": verify_certs,
        "request_timeout": 120,
    }
    if username and password:
        client_kwargs["basic_auth"] = (username, password)
    client = Elasticsearch(**client_kwargs)
    dimension = len(vectors[0])

    if recreate and client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
        print(f"elasticsearch index deleted: {index_name}")

    if not client.indices.exists(index=index_name):
        client.indices.create(
            index=index_name,
            settings={
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
            mappings={
                "dynamic": True,
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "document_name": {"type": "keyword"},
                    "source_path": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "page_start": {"type": "integer"},
                    "page_end": {"type": "integer"},
                    "content": {"type": "text"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": dimension,
                        "index": True,
                        "similarity": "cosine",
                    },
                    "benchmark": {"type": "boolean"},
                    "indexed_at": {"type": "date"},
                },
            },
        )
        print(f"elasticsearch index created: {index_name} dim={dimension}")
        client.cluster.health(index=index_name, wait_for_status="yellow", timeout="120s")

    actions = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        actions.append(
            {
                "_op_type": "index",
                "_index": index_name,
                "_id": chunk.chunk_id,
                "_source": {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "document_name": chunk.document_name,
                    "chunk_index": chunk.chunk_index,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "content": chunk.content,
                    "embedding": vector,
                    **chunk.metadata,
                },
            }
        )
    for batch_index, batch in enumerate(batched(actions, batch_size), start=1):
        success, errors = helpers.bulk(client, batch, refresh=False, raise_on_error=False)
        if errors:
            raise RuntimeError(f"Elasticsearch bulk index failed in batch {batch_index}: {errors[:3]}")
        print(f"elasticsearch bulk batch {batch_index}: rows={success}")
    client.indices.refresh(index=index_name)
    print(f"vector index complete: index={index_name} rows={len(actions)} dim={dimension}")


def delete_elasticsearch_index(
    *,
    url: str,
    username: str | None,
    password: str | None,
    verify_certs: bool,
    index_name: str,
) -> bool:
    try:
        from elasticsearch import Elasticsearch  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing elasticsearch. Install with: pip install -r scripts/requirements.txt") from exc

    client_kwargs: dict[str, Any] = {
        "hosts": [url],
        "verify_certs": verify_certs,
        "request_timeout": 120,
    }
    if username and password:
        client_kwargs["basic_auth"] = (username, password)
    client = Elasticsearch(**client_kwargs)
    if not client.indices.exists(index=index_name):
        print(f"elasticsearch index not found: {index_name}")
        return False
    client.indices.delete(index=index_name)
    print(f"elasticsearch index deleted: {index_name}")
    return True
