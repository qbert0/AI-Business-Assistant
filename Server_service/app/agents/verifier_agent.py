from fastapi import HTTPException

from app.agents.base import BaseAgent, AgentWorkflowState, clean_text, parse_json_object
from app.config import AGENT_SETTINGS
from app.services.model_service import create_inference


class VerifierAgent(BaseAgent):
    name = "verifier"
    stage = "verifying"
    start_message = "Dang doi chieu ban nhap voi context va kiem tra do tin cay."

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if not state.draft_answer:
            state.verified_answer = ""
            state.verification_notes = ""
            return state

        if not state.organization_id or not state.contexts:
            state.verified_answer = state.draft_answer
            state.verification_notes = ""
            return state

        if sum(len(item.get("content") or "") for item in state.contexts) > AGENT_SETTINGS.verifier.max_context_chars_for_model_verify:
            state.verified_answer = state.draft_answer
            state.verification_notes = "Skipped model verification because the retrieved context was too long."
            return state

        try:
            inference = create_inference(
                {
                    "conversation_id": state.session_id,
                    "organization_id": state.organization_id,
                    "user_id": state.user_id,
                    "use_case": "chat_multi_agent",
                    "question": (
                        f"Original question:\n{state.question}\n\n"
                        f"Current draft answer:\n{state.draft_answer}"
                    ),
                    "history": [],
                    "external_contexts": state.contexts,
                    "system_prompt": (
                        "You are the verification agent. "
                        "Check the current draft answer against the trusted context. "
                        "Keep only claims that are supported by the trusted context. "
                        "If the context is insufficient, say what is missing and revise the answer so it stays grounded. "
                        "Be brief and produce the final revised answer directly. "
                        "Return ONLY one valid JSON object with no markdown, "
                        'using this schema: {"is_grounded":true,"revised_answer":"...","notes":"..."}. '
                        "revised_answer must be directly user-facing and must stay in the same language as the user's question unless the user explicitly asked for another language."
                    ),
                    "max_tokens": AGENT_SETTINGS.verifier.max_completion_tokens,
                    "metadata": {
                        "phase": "verify_answer",
                        "agent": self.name,
                        "organization_id": state.organization_id,
                        "search_hit_count": len(state.search_hits),
                    },
                }
            )
            response_text = (((inference or {}).get("response") or {}).get("response_text") or "").strip()
            payload = parse_json_object(response_text)
            revised_answer = clean_text(payload.get("revised_answer"))
            notes = clean_text(payload.get("notes"))

            state.verified_answer = revised_answer or state.draft_answer
            state.verification_notes = notes
        except HTTPException:
            state.verified_answer = state.draft_answer
            state.verification_notes = ""

        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        if state.verified_answer:
            return "Da doi chieu xong ban nhap voi context truy xuat."
        return "Khong co ban nhap de doi chieu."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "has_verified_answer": bool(state.verified_answer),
            "verification_notes": state.verification_notes,
        }
