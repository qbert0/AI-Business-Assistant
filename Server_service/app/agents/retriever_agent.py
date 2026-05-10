from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent, AgentWorkflowEvent, AgentWorkflowState
from app.config import AGENT_SETTINGS
from app.entities.chat import CitationEntity
from app.entities.search import SearchHitEntity
from app.services.rag_search_service import build_group_id, query_rag_facts, query_rag_nodes


class RetrieverAgent(BaseAgent):
    name = "retriever"
    stage = "retrieval"
    start_message = "Đang truy xuất facts và nodes liên quan trong kho tri thức nội bộ."
    METADATA_PREVIEW_TEXT_LIMIT = 4000

    def __init__(self, db: Session) -> None:
        self.db = db

    def _build_metadata_preview_text(self, content_text: str | None) -> str:
        if not content_text:
            return ""
        return content_text[: self.METADATA_PREVIEW_TEXT_LIMIT]

    def _to_citations(self, hits: list[SearchHitEntity]) -> list[CitationEntity]:
        citations: list[CitationEntity] = []
        seen: set[tuple[str, str]] = set()
        for hit in hits:
            document_id = hit.document.get("document_id") or hit.document_id
            file_name = hit.document.get("file_name") or hit.document.get("document_name") or hit.document_id
            source_url = hit.document.get("source_url") or ""
            citation_key = (str(document_id), str(source_url))
            if citation_key in seen:
                continue
            seen.add(citation_key)
            citations.append(
                CitationEntity(
                    document_id=document_id,
                    file_name=file_name,
                    source_url=source_url,
                )
            )
        return citations

    def _build_relevant_excerpt(self, content: str) -> str:
        normalized_content = (content or "").strip()
        if len(normalized_content) <= AGENT_SETTINGS.retrieval.context_char_limit:
            return normalized_content
        return normalized_content[: AGENT_SETTINGS.retrieval.context_char_limit]

    def _to_context_items(self, hits: list[SearchHitEntity], state: AgentWorkflowState) -> list[dict]:
        context_items: list[dict] = []
        for hit in hits[: AGENT_SETTINGS.retrieval.max_context_items]:
            document = hit.document or {}
            content = (
                document.get("content_text")
                or document.get("snippet")
                or document.get("fact")
                or document.get("summary")
                or ""
            )
            if not content:
                continue
            excerpt = self._build_relevant_excerpt(content)
            if not excerpt:
                continue
            source_url = document.get("source_url") or ""
            hit_type = document.get("hit_type") or "graph"
            hit_uuid = document.get("uuid") or hit.document_id
            context_items.append(
                {
                    "title": document.get("document_name") or document.get("file_name") or document.get("name") or hit.document_id,
                    "content": excerpt,
                    "source": source_url or f"rag://{hit_type}/{hit_uuid}",
                    "metadata": {
                        "document_id": document.get("document_id") or hit.document_id,
                        "chunk_id": document.get("chunk_id"),
                        "episode_uuid": document.get("episode_uuid"),
                        "hit_type": hit_type,
                        "score": hit.score,
                    },
                }
            )
        return context_items

    def _build_queries(self, state: AgentWorkflowState) -> list[str]:
        queries: list[str] = []
        for candidate in state.retrieval_queries:
            cleaned = (candidate or "").strip()
            if cleaned and cleaned not in queries:
                queries.append(cleaned)
        if not queries:
            queries.append(state.question)
        return queries[: AGENT_SETTINGS.retrieval.max_queries_per_attempt]

    def _merge_hits(self, batches: list[list[SearchHitEntity]]) -> list[SearchHitEntity]:
        merged: dict[str, SearchHitEntity] = {}
        for hits in batches:
            for hit in hits:
                hit_key = (
                    hit.document.get("hit_key")
                    or hit.document.get("chunk_id")
                    or hit.document.get("uuid")
                    or hit.document.get("document_id")
                    or hit.document_id
                )
                current = merged.get(str(hit_key))
                current_score = current.score if current else None
                incoming_score = hit.score if hit.score is not None else float("-inf")
                stored_score = current_score if current_score is not None else float("-inf")
                if current is None or incoming_score > stored_score:
                    merged[str(hit_key)] = hit
        return sorted(
            merged.values(),
            key=lambda item: item.score if item.score is not None else float("-inf"),
            reverse=True,
        )[: AGENT_SETTINGS.retrieval.max_merged_hits]

    def _search(self, organization_id: str, queries: list[str]) -> list[SearchHitEntity]:
        batches: list[list[SearchHitEntity]] = []
        for query in queries:
            if not query:
                continue
            batches.append(query_rag_facts(organization_id, query, limit=AGENT_SETTINGS.retrieval.hits_per_query))
            batches.append(query_rag_nodes(organization_id, query, limit=AGENT_SETTINGS.retrieval.hits_per_query))
        return self._merge_hits(batches)

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if not state.organization_id or not state.needs_document_search:
            state.search_hits = []
            state.citations = []
            state.contexts = []
            return state

        queries = self._build_queries(state)
        state.metadata["retrieval_backend"] = "rag_search"
        state.metadata["retrieval_group_id"] = build_group_id(state.organization_id)

        try:
            hits = self._search(state.organization_id, queries)
        except HTTPException:
            hits = []

        state.search_hits = hits
        state.citations = self._to_citations(hits)
        state.contexts = self._to_context_items(hits, state)
        fact_hits = sum(1 for hit in hits if (hit.document or {}).get("hit_type") == "fact")
        node_hits = sum(1 for hit in hits if (hit.document or {}).get("hit_type") == "node")
        state.search_attempts.append(
            {
                "attempt": len(state.search_attempts) + 1,
                "retrieval_queries": list(state.retrieval_queries),
                "hit_count": len(hits),
                "fact_hit_count": fact_hits,
                "node_hit_count": node_hits,
            }
        )
        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        if not state.organization_id or not state.needs_document_search:
            return "Câu hỏi này không cần truy xuất tài liệu."
        if state.search_hits:
            return "Đã tìm thấy facts, nodes, và ngữ cảnh liên quan để đưa vào trả lời."
        return "Chưa tìm thấy dữ kiện phù hợp trong kho tri thức nội bộ."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "attempt": len(state.search_attempts),
            "retrieval_queries": state.retrieval_queries,
            "search_hit_count": len(state.search_hits),
            "fact_hit_count": sum(1 for hit in state.search_hits if (hit.document or {}).get("hit_type") == "fact"),
            "node_hit_count": sum(1 for hit in state.search_hits if (hit.document or {}).get("hit_type") == "node"),
            "context_count": len(state.contexts),
        }

    def extra_events(self, state: AgentWorkflowState) -> list[AgentWorkflowEvent]:
        if not state.organization_id or not state.needs_document_search:
            return []

        return [
            AgentWorkflowEvent(
                event_type="search_results",
                stage=self.stage,
                agent=self.name,
                message="Đã cập nhật kết quả truy xuất RAG.",
                payload={
                    "retrieval_queries": state.retrieval_queries,
                    "retrieval_backend": state.metadata.get("retrieval_backend"),
                    "group_id": state.metadata.get("retrieval_group_id"),
                    "hits": [
                        {
                            "document_id": hit.document_id,
                            "file_name": hit.document.get("file_name") or hit.document_id,
                            "document_name": hit.document.get("document_name") or hit.document.get("file_name") or hit.document_id,
                            "source_url": hit.document.get("source_url") or "",
                            "chunk_id": hit.document.get("chunk_id"),
                            "hit_type": hit.document.get("hit_type"),
                            "score": hit.score,
                            "document": hit.document,
                        }
                        for hit in state.search_hits
                    ],
                    "citations": [
                        {
                            "document_id": citation.document_id,
                            "file_name": citation.file_name,
                            "source_url": citation.source_url,
                        }
                        for citation in state.citations
                    ],
                },
            )
        ]
