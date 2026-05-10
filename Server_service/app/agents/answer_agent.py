from fastapi import HTTPException

from app.agents.base import BaseAgent, AgentWorkflowState, clean_text, format_feedback_guidance, parse_json_object
from app.config import AGENT_SETTINGS
from app.services.model_service import create_inference


class AnswerAgent(BaseAgent):
    name = "answerer"
    stage = "drafting"
    start_message = "Đang soạn bản nháp câu trả lời từ ngữ cảnh hiện có."

    def _extract_answer_text(self, response_text: str) -> str:
        payload = parse_json_object(response_text)
        if payload:
            answer = clean_text(payload.get("answer"))
            if answer:
                return answer
        return response_text.strip()

    def _build_compact_contexts(self, state: AgentWorkflowState) -> list[dict]:
        compact_contexts: list[dict] = []
        for item in state.contexts[: AGENT_SETTINGS.answerer.compact_context_items]:
            compact_contexts.append(
                {
                    **item,
                    "content": (item.get("content") or "")[: AGENT_SETTINGS.answerer.compact_context_chars],
                }
            )
        return compact_contexts

    def _run_inference(self, state: AgentWorkflowState, contexts: list[dict]) -> str:
        feedback_guidance = format_feedback_guidance(state.feedback_contexts)
        answering_mode_prompt = (
            "The user is asking for a report-style response. "
            "Draft a fuller markdown-ready report body with clear sections, meaningful synthesis, and all important grounded figures that support the requested report. "
            "Do not be terse. Prefer completeness over brevity, while staying grounded in the trusted context. "
            if state.wants_report_output
            else "Answer directly and keep the response concise. "
        )
        inference = create_inference(
            {
                "conversation_id": state.session_id,
                "organization_id": state.organization_id,
                "user_id": state.user_id,
                "use_case": "chat_multi_agent",
                "question": state.question,
                "history": state.history,
                "external_contexts": contexts,
                "system_prompt": (
                    "You are the answering agent for an internal business assistant. "
                    f"Current plan: {state.plan_summary or 'Provide a clear, concise, well-structured answer.'} "
                    "If trusted context is provided, rely only on that context for factual claims. "
                    "If the context is insufficient, explicitly say what is missing. "
                    "Do not invent unsupported details. "
                    + answering_mode_prompt
                    + "Use minimal internal reasoning before answering. "
                    + (f"\n\n{feedback_guidance}\nRemember: feedback is guidance about answer quality, not factual evidence." if feedback_guidance else "")
                    + " "
                    + "Return ONLY one valid JSON object with no markdown, using this schema: "
                    + '{"answer":"..."}. '
                    + "The answer value must be directly user-facing and must stay in the same language as the user's question unless the user explicitly asks for another language."
                ),
                "max_tokens": AGENT_SETTINGS.answerer.max_completion_tokens,
                "metadata": {
                    "phase": "draft_answer",
                    "agent": self.name,
                    "organization_id": state.organization_id,
                    "search_hit_count": len(state.search_hits),
                    "context_count": len(contexts),
                },
            }
        )
        response_text = (((inference or {}).get("response") or {}).get("response_text") or "").strip()
        return self._extract_answer_text(response_text)

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if state.organization_id and not state.contexts:
            state.metadata["answerer_failure_reason"] = "no_retrieved_context"
            state.draft_answer = ""
            return state

        try:
            state.draft_answer = self._run_inference(state, state.contexts)
            if not state.draft_answer and state.contexts:
                state.draft_answer = self._run_inference(state, self._build_compact_contexts(state))
            if state.draft_answer:
                state.metadata.pop("answerer_failure_reason", None)
            else:
                state.metadata["answerer_failure_reason"] = "empty_model_output"
        except HTTPException:
            state.metadata["answerer_failure_reason"] = "model_inference_http_error"
            state.draft_answer = ""

        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        if state.draft_answer:
            return "Đã soạn xong bản nháp câu trả lời."
        return "Chưa tạo được bản nháp câu trả lời từ mô hình."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "has_draft_answer": bool(state.draft_answer),
            "draft_answer_length": len(state.draft_answer),
        }
