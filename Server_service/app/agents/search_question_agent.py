import json

from fastapi import HTTPException

from app.agents.base import BaseAgent, AgentWorkflowState, coerce_string_list, format_feedback_guidance, parse_json_object
from app.config import AGENT_SETTINGS
from app.services.model_service import create_inference


class SearchQuestionAgent(BaseAgent):
    name = "questioner"
    stage = "questioning"
    start_message = "Đang xây dựng lại truy vấn tìm kiếm để tìm facts và nodes phù hợp."

    def _previous_attempts_summary(self, state: AgentWorkflowState) -> str:
        if not state.search_attempts:
            return "No previous retrieval attempts."

        summary = [
            {
                "attempt": item.get("attempt"),
                "retrieval_queries": item.get("retrieval_queries"),
                "hit_count": item.get("hit_count"),
                "fact_hit_count": item.get("fact_hit_count"),
                "node_hit_count": item.get("node_hit_count"),
            }
            for item in state.search_attempts[-3:]
        ]
        return json.dumps(summary, ensure_ascii=False)

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if not state.organization_id or not state.needs_document_search:
            state.retrieval_queries = [state.question]
            return state

        attempt_number = len(state.search_attempts) + 1
        feedback_guidance = format_feedback_guidance(state.feedback_contexts)
        try:
            inference = create_inference(
                {
                    "conversation_id": state.session_id,
                    "organization_id": state.organization_id,
                    "user_id": state.user_id,
                    "use_case": "chat_multi_agent",
                    "question": state.question,
                    "history": state.history[-AGENT_SETTINGS.questioner.history_limit:],
                    "external_contexts": [],
                    "system_prompt": (
                        "You are the search question agent for an internal business assistant. "
                        "Your job is to propose retrieval queries that help the retriever find relevant facts, nodes, and grounded evidence in the internal knowledge graph. "
                        "Return ONLY one valid JSON object with no markdown, "
                        'using this schema: {"retrieval_queries":["..."]}. '
                        f"retrieval_queries must contain at most {AGENT_SETTINGS.retrieval.max_queries_per_attempt} alternative retrieval queries, "
                        "all in the same language as the user's question. "
                        "Each query should be short, concrete, and meaningfully different from the others. "
                        "Do not repeat the same wording from unsuccessful attempts if prior searches returned no hits. "
                        f"This is retrieval attempt #{attempt_number}. "
                        f"Previous retrieval attempts: {self._previous_attempts_summary(state)}"
                        + (f"\n\n{feedback_guidance}" if feedback_guidance else "")
                    ),
                    "metadata": {
                        "phase": "search_question",
                        "agent": self.name,
                        "organization_id": state.organization_id,
                        "attempt": attempt_number,
                    },
                }
            )
            response_text = (((inference or {}).get("response") or {}).get("response_text") or "").strip()
            payload = parse_json_object(response_text)
            state.retrieval_queries = coerce_string_list(payload.get("retrieval_queries"))[
                : AGENT_SETTINGS.retrieval.max_queries_per_attempt
            ]
        except HTTPException:
            state.retrieval_queries = state.retrieval_queries or [state.question]

        if not state.retrieval_queries:
            state.retrieval_queries = [state.question]

        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        return "Đã tạo bộ truy vấn cho lượt tìm kiếm này."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "attempt": len(state.search_attempts) + 1,
            "retrieval_queries": state.retrieval_queries,
        }
