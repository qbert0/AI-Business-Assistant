import re

from fastapi import HTTPException

from app.agents.base import BaseAgent, AgentWorkflowState, clean_text, coerce_bool, coerce_string_list, format_feedback_guidance, parse_json_object
from app.config import AGENT_SETTINGS
from app.services.model_service import create_inference


class PlannerAgent(BaseAgent):
    name = "planner"
    stage = "planning"
    start_message = "Đang phân tích câu hỏi và lập kế hoạch truy xuất."
    REPORT_PATTERN = re.compile(
        r"(?i)\b("
        r"bao\s*cao|báo\s*cáo|report|pdf|xuat\s*pdf|xuất\s*pdf|tai\s*pdf|tải\s*pdf|"
        r"tao\s*bao\s*cao|tạo\s*báo\s*cáo|viet\s*bao\s*cao|viết\s*báo\s*cáo|"
        r"lap\s*bao\s*cao|lập\s*báo\s*cáo|generate\s+report|export\s+report"
        r")\b"
    )

    def _detect_report_request(self, question: str) -> bool:
        lowered = clean_text(question).lower()
        if not lowered:
            return False
        if any(token in lowered for token in ("xuất pdf", "xuat pdf", " file pdf", " bản pdf", "ban pdf")):
            return True
        if self.REPORT_PATTERN.search(lowered):
            return True
        return False

    def _default_report_title(self, question: str) -> str:
        cleaned = re.sub(r"\s+", " ", clean_text(question)).strip("?.! ")
        if not cleaned:
            return "Bao cao tong hop"
        if len(cleaned) <= 96:
            return cleaned
        return cleaned[:93].rstrip() + "..."

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        heuristic_report_request = self._detect_report_request(state.question)
        if not state.organization_id:
            state.plan_summary = (
                "Act as a personal workspace guide for the product. "
                "Use the provided system guidance, the user's available workspace access, and the chat history. "
                "If the question requires internal company documents, policies, or indexed organization knowledge, "
                "redirect the user to the relevant organization workspace instead of answering as if grounded retrieval had happened."
            )
            state.retrieval_queries = [state.question]
            state.needs_document_search = False
            state.wants_report_output = False
            state.report_title_hint = ""
            return state

        feedback_guidance = format_feedback_guidance(state.feedback_contexts)

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
                        'using this schema: {"plan_summary":"...","retrieval_queries":["..."],"needs_document_search":true,"wants_report_output":false,"report_title_hint":"..."}. '
                        "plan_summary must be concise and describe the intended answering strategy in English. "
                        f"retrieval_queries must contain at most {AGENT_SETTINGS.retrieval.max_queries_per_attempt} short retrieval queries, "
                        "all written in the same language as the user's question. "
                        "Each query should represent a different useful phrasing or retrieval angle for the same request. "
                        "Set needs_document_search to true when grounded retrieval from the organization's knowledge graph is required to answer reliably. "
                        "Set wants_report_output to true when the user explicitly asks to create, export, or receive a report or PDF. "
                        "When wants_report_output is true, report_title_hint should be a concise Vietnamese title suitable for the final report heading. "
                        + (f"\n\n{feedback_guidance}" if feedback_guidance else "")
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
            state.wants_report_output = coerce_bool(payload.get("wants_report_output"), heuristic_report_request)
            state.report_title_hint = clean_text(payload.get("report_title_hint"))
            # For organization chat, retrieval remains mandatory. The planner can
            # shape the strategy, but it should not short-circuit the grounded
            # retrieval loop entirely.
            state.needs_document_search = True
        except HTTPException:
            state.plan_summary = ""
            state.needs_document_search = True
            state.wants_report_output = heuristic_report_request

        if not state.plan_summary:
            state.plan_summary = "Retrieve the most relevant internal facts and graph-grounded evidence, then synthesize a concise grounded answer."
        if not state.retrieval_queries:
            state.retrieval_queries = [state.question]
        if heuristic_report_request:
            state.wants_report_output = True
        if state.wants_report_output and not state.report_title_hint:
            state.report_title_hint = self._default_report_title(state.question)

        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        if state.needs_document_search:
            return "Đã xác định kế hoạch và bộ truy vấn cho bước truy xuất tri thức."
        return "Đã xác định kế hoạch trả lời trực tiếp từ hội thoại hiện có."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "plan_summary": state.plan_summary,
            "retrieval_queries": state.retrieval_queries,
            "needs_document_search": state.needs_document_search,
            "wants_report_output": state.wants_report_output,
            "report_title_hint": state.report_title_hint,
        }
