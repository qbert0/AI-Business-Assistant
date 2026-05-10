from fastapi import HTTPException

from app.agents.base import BaseAgent, AgentWorkflowState, clean_text, coerce_string_list, parse_json_object
from app.config import AGENT_SETTINGS
from app.services.model_service import create_inference


class PlannerAgent(BaseAgent):
    name = "planner"
    stage = "planning"
    start_message = "Dang lap ke hoach va dat cau hoi truy xuat."

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if not state.organization_id:
            state.plan_summary = "Answer directly from the user's question and the available chat history."
            state.retrieval_queries = [state.question]
            state.needs_document_search = False
            return state

        try:
            inference = create_inference(
                {
                    "conversation_id": state.session_id,
                    "organization_id": state.organization_id,
                    "user_id": state.user_id,
                    "use_case": "chat_multi_agent",
                    "question": state.question,
                    "history": state.history[-AGENT_SETTINGS.planner.history_limit:],
                    "external_contexts": [],
                    "system_prompt": (
                        "You are the planning agent for an internal business assistant. "
                        "Analyze the user's request and return ONLY one valid JSON object with no markdown, "
                        'using this schema: {"plan_summary":"...","retrieval_queries":["..."],"needs_document_search":true}. '
                        "plan_summary must be concise and describe the intended answering strategy in English. "
                        f"retrieval_queries must contain at most {AGENT_SETTINGS.retrieval.max_queries_per_attempt} short retrieval queries, "
                        "all written in the same language as the user's question. "
                        "Each query should represent a different useful phrasing or retrieval angle for the same request. "
                        "Set needs_document_search to true when internal documents are required to answer reliably."
                    ),
                    "metadata": {
                        "phase": "planner",
                        "agent": self.name,
                        "organization_id": state.organization_id,
                    },
                }
            )
            response_text = (((inference or {}).get("response") or {}).get("response_text") or "").strip()
            payload = parse_json_object(response_text)
            state.plan_summary = clean_text(payload.get("plan_summary"))
            state.retrieval_queries = coerce_string_list(payload.get("retrieval_queries"))[
                : AGENT_SETTINGS.retrieval.max_queries_per_attempt
            ]
            # For organization chat, retrieval remains mandatory. The planner can
            # shape the strategy, but it should not short-circuit the document
            # search loop entirely.
            state.needs_document_search = True
        except HTTPException:
            state.plan_summary = ""
            state.needs_document_search = True

        if not state.plan_summary:
            state.plan_summary = "Retrieve the most relevant internal documents, then synthesize a concise grounded answer."
        if not state.retrieval_queries:
            state.retrieval_queries = [state.question]

        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        if state.needs_document_search:
            return "Da co ke hoach va truy van tim kiem cho buoc truy xuat tai lieu."
        return "Da co ke hoach tra loi truc tiep tu hoi thoai hien co."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "plan_summary": state.plan_summary,
            "retrieval_queries": state.retrieval_queries,
            "needs_document_search": state.needs_document_search,
        }
