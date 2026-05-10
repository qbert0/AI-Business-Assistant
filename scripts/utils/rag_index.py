from __future__ import annotations

from scripts.utils.benchmark_pdf import TextChunk
from scripts.utils.http_client import post_json


def ingest_graph(
    chunks: list[TextChunk],
    *,
    rag_url: str,
    organization_id: str,
    timeout: float,
    retries: int,
) -> None:
    by_document: dict[str, list[TextChunk]] = {}
    for chunk in chunks:
        by_document.setdefault(chunk.document_id, []).append(chunk)

    for document_id, document_chunks in by_document.items():
        first = document_chunks[0]
        result = post_json(
            rag_url,
            "/ingest/chunks",
            {
                "document_id": document_id,
                "document_name": first.document_name,
                "source": "benchmark-cli",
                "source_description": "Benchmark PDF dataset",
                "metadata": {
                    "benchmark": True,
                    "organization_id": organization_id,
                    "document_name": first.document_name,
                    "chunk_count": len(document_chunks),
                },
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                    }
                    for chunk in document_chunks
                ],
            },
            timeout=timeout,
            retries=retries,
        )
        print(
            "graph ingest accepted: "
            f"document={first.document_name} chunks={len(document_chunks)} message_id={result.get('message_id')}"
        )
