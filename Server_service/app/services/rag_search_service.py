import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app import messages
from app.config import RAG_SEARCH_TIMEOUT, RAG_SERVICE_URL
from app.entities.search import SearchHitEntity


def _request_json(path: str, payload: dict) -> dict:
    request = Request(
        f"{RAG_SERVICE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=RAG_SEARCH_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{messages.RAG_SERVICE_UNAVAILABLE}: {detail or exc.reason}",
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=messages.RAG_SERVICE_UNAVAILABLE,
        ) from exc


def build_group_id(organization_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", str(organization_id or "")).strip("-")
    cleaned = cleaned or "unknown-organization"
    return f"org-{cleaned}"


def _coerce_text(value: object, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _normalize_hit(item: dict, *, hit_type: str, group_id: str) -> SearchHitEntity:
    document_id = _coerce_text(item.get("document_id") or item.get("uuid"))
    document_name = _coerce_text(
        item.get("document_name") or item.get("file_name") or item.get("name"),
        document_id or ("Graph fact" if hit_type == "fact" else "Graph node"),
    )
    chunk_id = _coerce_text(item.get("chunk_id")) or None
    source_url = _coerce_text(item.get("source_url"))
    score = item.get("score")
    hit_uuid = _coerce_text(item.get("uuid"), document_id)
    hit_key = _coerce_text(item.get("hit_key"), f"{hit_type}:{chunk_id or hit_uuid}")

    content_text = _coerce_text(
        item.get("content_text") or item.get("snippet") or item.get("fact") or item.get("summary")
    )

    document = {
        "document_id": document_id,
        "document_name": document_name,
        "file_name": document_name,
        "source_url": source_url,
        "chunk_id": chunk_id,
        "score": score,
        "content_text": content_text,
        "snippet": _coerce_text(item.get("snippet"), content_text),
        "summary": _coerce_text(item.get("summary")),
        "fact": _coerce_text(item.get("fact")),
        "hit_type": hit_type,
        "uuid": hit_uuid,
        "episode_uuid": _coerce_text(item.get("episode_uuid")) or None,
        "episode_name": _coerce_text(item.get("episode_name")) or None,
        "labels": item.get("labels") or [],
        "group_id": _coerce_text(item.get("group_id"), group_id),
        "source_node_uuid": _coerce_text(item.get("source_node_uuid")) or None,
        "target_node_uuid": _coerce_text(item.get("target_node_uuid")) or None,
        "hit_key": hit_key,
    }

    return SearchHitEntity(
        index_name=f"rag:{group_id}",
        document_id=document_id or hit_uuid,
        score=float(score) if isinstance(score, (int, float)) else None,
        document=document,
    )


def query_rag_nodes(organization_id: str, query: str, *, limit: int = 8) -> list[SearchHitEntity]:
    group_id = build_group_id(organization_id)
    response = _request_json(
        "/search/nodes",
        {
            "query": query,
            "limit": limit,
            "group_id": group_id,
        },
    )
    data = response.get("results", response.get("data", response))
    if not isinstance(data, list):
        return []
    return [_normalize_hit(item, hit_type="node", group_id=group_id) for item in data if isinstance(item, dict)]


def query_rag_facts(
    organization_id: str,
    query: str,
    *,
    limit: int = 8,
    center_node_uuid: str | None = None,
) -> list[SearchHitEntity]:
    group_id = build_group_id(organization_id)
    response = _request_json(
        "/search/facts",
        {
            "query": query,
            "limit": limit,
            "group_id": group_id,
            "center_node_uuid": center_node_uuid,
        },
    )
    data = response.get("results", response.get("data", response))
    if not isinstance(data, list):
        return []
    return [_normalize_hit(item, hit_type="fact", group_id=group_id) for item in data if isinstance(item, dict)]
