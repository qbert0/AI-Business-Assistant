from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent, AgentWorkflowEvent, AgentWorkflowState
from app.config import AGENT_SETTINGS
from app.entities.chat import CitationEntity
from app.entities.search import SearchHitEntity
from app.services.search_service import query_documents


class RetrieverAgent(BaseAgent):
    name = "retriever"
    stage = "retrieval"
    start_message = "Đang tìm tài liệu liên quan trong kho nội bộ."
    METADATA_PREVIEW_TEXT_LIMIT = 4000

    def __init__(self, db: Session) -> None:
        self.db = db

    def _build_metadata_preview_text(self, content_text: str | None) -> str:
        if not content_text:
            return ""
        return content_text[: self.METADATA_PREVIEW_TEXT_LIMIT]

    def _to_citations(self, hits: list[SearchHitEntity]) -> list[CitationEntity]:
        return [
            CitationEntity(
                document_id=hit.document.get("document_id") or hit.document_id,
                file_name=hit.document.get("file_name") or hit.document_id,
                source_url=hit.document.get("source_url") or "",
            )
            for hit in hits
        ]

    def _build_relevant_excerpt(self, content: str) -> str:
        normalized_content = (content or "").strip()
        if len(normalized_content) <= AGENT_SETTINGS.retrieval.context_char_limit:
            return normalized_content
        return normalized_content[: AGENT_SETTINGS.retrieval.context_char_limit]

    def _to_context_items(self, hits: list[SearchHitEntity], state: AgentWorkflowState) -> list[dict]:
        context_items: list[dict] = []
        for hit in hits[: AGENT_SETTINGS.retrieval.max_context_items]:
            document = hit.document or {}
            content = document.get("content_text") or ""
            if not content:
                metadata = document.get("metadata") or {}
                content = metadata.get("content_text") or metadata.get("preview_text") or ""
            if not content:
                continue
            excerpt = self._build_relevant_excerpt(content)
            if not excerpt:
                continue
            context_items.append(
                {
                    "title": document.get("file_name") or hit.document_id,
                    "content": excerpt,
                    "source": document.get("source_url") or "",
                    "metadata": {
                        "document_id": hit.document_id,
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
                current = merged.get(hit.document_id)
                current_score = current.score if current else None
                incoming_score = hit.score if hit.score is not None else float("-inf")
                stored_score = current_score if current_score is not None else float("-inf")
                if current is None or incoming_score > stored_score:
                    merged[hit.document_id] = hit
        return sorted(
            merged.values(),
            key=lambda item: item.score if item.score is not None else float("-inf"),
            reverse=True,
        )[: AGENT_SETTINGS.retrieval.max_merged_hits]

    def _search(self, index_name: str, queries: list[str]) -> list[SearchHitEntity]:
        batches = [
            query_documents(index_name, query, size=AGENT_SETTINGS.retrieval.hits_per_query)
            for query in queries
            if query
        ]
        return self._merge_hits(batches)

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if not state.organization_id or not state.needs_document_search:
            state.search_hits = []
            state.citations = []
            state.contexts = []
            return state

        index_name = f"org-{state.organization_id}-documents"
        queries = self._build_queries(state)

        try:
            hits = self._search(index_name, queries)
        except HTTPException:
            hits = []

        state.search_hits = hits
        state.citations = self._to_citations(hits)
        state.contexts = self._to_context_items(hits, state)
        state.search_attempts.append(
            {
                "attempt": len(state.search_attempts) + 1,
                "retrieval_queries": list(state.retrieval_queries),
                "hit_count": len(hits),
            }
        )
        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        if not state.organization_id or not state.needs_document_search:
            return "Câu hỏi này không cần truy xuất tài liệu."
        if state.search_hits:
            return "Đã tìm thấy tài liệu liên quan để đưa vào ngữ cảnh trả lời."
        return "Chưa tìm thấy tài liệu phù hợp trong kho nội bộ."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "attempt": len(state.search_attempts),
            "retrieval_queries": state.retrieval_queries,
            "search_hit_count": len(state.search_hits),
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
                message="Đã cập nhật kết quả tìm tài liệu.",
                payload={
                    "retrieval_queries": state.retrieval_queries,
                    "hits": [
                        {
                            "document_id": hit.document_id,
                            "file_name": hit.document.get("file_name") or hit.document_id,
                            "source_url": hit.document.get("source_url") or "",
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
