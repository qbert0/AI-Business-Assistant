import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app import messages
from app.config import SEARCH_SERVICE_TIMEOUT, SEARCH_SERVICE_URL
from app.entities import database as db_entities
from app.entities.search import SearchDocumentEntity, SearchHitEntity
from app.repositories.common import parse_json_dict


def _request_json(path: str, payload: dict) -> dict:
    request = Request(
        f"{SEARCH_SERVICE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=SEARCH_SERVICE_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{messages.SEARCH_SERVICE_UNAVAILABLE}: {detail or exc.reason}",
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=messages.SEARCH_SERVICE_UNAVAILABLE,
        ) from exc


def index_document(document: db_entities.Document) -> SearchDocumentEntity:
    payload = {
        "index_name": document.vector_index or f"org-{document.organization_id}-documents",
        "document_id": document.id,
        "document": {
            "organization_id": document.organization_id,
            "document_id": document.id,
            "uploaded_by_user_id": document.uploaded_by_user_id,
            "file_name": document.file_name,
            "source_url": document.source_url,
            "status": document.status,
            "chunk_count": int(document.chunk_count or 0),
            "embedding_model": document.embedding_model,
            "metadata": parse_json_dict(document.metadata_json),
        },
        "refresh": True,
    }
    response = _request_json("/search/documents", payload)
    data = response.get("data", response)
    return SearchDocumentEntity(
        index_name=data.get("index_name", payload["index_name"]),
        document_id=data.get("document_id", payload["document_id"]),
        document=data.get("document", payload["document"]),
    )


def query_documents(index_name: str, query: str, *, size: int = 3) -> list[SearchHitEntity]:
    response = _request_json(
        "/search/documents/query",
        {
            "index_name": index_name,
            "query": query,
            "size": size,
            "fields": ["file_name^3", "source_url", "metadata.*", "status"],
        },
    )
    data = response.get("data", response)
    if not isinstance(data, list):
        return []
    return [
        SearchHitEntity(
            index_name=item.get("index_name", index_name),
            document_id=item.get("document_id", ""),
            score=item.get("score"),
            document=item.get("document") or {},
        )
        for item in data
    ]
