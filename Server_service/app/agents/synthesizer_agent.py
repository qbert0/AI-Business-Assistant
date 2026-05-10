from fastapi import HTTPException

from app.agents.base import BaseAgent, AgentWorkflowState, clean_text, parse_json_object
from app.config import AGENT_SETTINGS
from app.services.model_service import create_inference


class SynthesizerAgent(BaseAgent):
    name = "synthesizer"
    stage = "synthesizing"
    start_message = "Dang tong hop cau tra loi cuoi cung."

    def _extract_answer_text(self, response_text: str) -> str:
        payload = parse_json_object(response_text)
        if payload:
            answer = clean_text(payload.get("answer"))
            if answer:
                return answer
        return response_text.strip()

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        candidate = (state.verified_answer or state.draft_answer or "").strip()
        if not candidate:
            state.answer = ""
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
                        f"Candidate answer:\n{candidate}\n\n"
                        f"Verification notes:\n{state.verification_notes or 'None'}"
                    ),
                    "history": [],
                    "external_contexts": [],
                    "system_prompt": (
                        "You are the synthesizer agent for an internal business assistant. "
                        "Rewrite the candidate answer into a polished final reply that feels complete and natural in conversation. "
                        "Keep the meaning and factual claims unchanged. "
                        "Do not add new facts, citations, or unsupported details. "
                        "Prefer a fuller answer over a one-line fragment. "
                        "In most cases, write 2 to 4 sentences: "
                        "first answer the question directly, "
                        "then add a brief supporting or clarifying sentence based only on the candidate answer and verification notes, "
                        "and optionally end with a short limitation or scope note if it is already implied by the candidate answer. "
                        "Do not pad with generic filler, but do make the reply feel complete. "
                        "Use the same language as the user's question unless the user explicitly asked for another language. "
                        "Examples:\n"
                        'Question: "Thông tư về thời hạn bảo quản tài liệu được ban hành vào ngày bao nhiêu?"\n'
                        'Candidate answer: "19 tháng 12 năm 2022."\n'
                        'Verification notes: "The document header shows the issuance date."\n'
                        'Output: {"answer":"Thông tư được ban hành vào ngày 19 tháng 12 năm 2022. Thông tin này xuất hiện ngay ở phần đầu văn bản, tại dòng ghi ngày ban hành của thông tư."}\n'
                        'Question: "Hồ sơ gốc được bảo quản bao lâu?"\n'
                        'Candidate answer: "Theo Thông tư 10/2022/TT-BNV, hồ sơ gốc được bảo quản trong vòng 10 năm."\n'
                        'Verification notes: "Grounded in the retrieved regulation."\n'
                        'Output: {"answer":"Theo Thông tư 10/2022/TT-BNV, thời hạn bảo quản hồ sơ gốc là 10 năm. Đây là mốc được xác định theo quy định trong tài liệu đã truy xuất, nên nếu bạn cần áp dụng cho một loại hồ sơ cụ thể thì mình có thể đối chiếu tiếp đúng nhóm hồ sơ đó."}\n'
                        'Question: "Công ty có chính sách du hành liên sao không?"\n'
                        'Candidate answer: "Hiện chưa có đủ thông tin trong tài liệu đã truy xuất để khẳng định công ty có chính sách này."\n'
                        'Verification notes: "Insufficient grounded evidence."\n'
                        'Output: {"answer":"Hiện mình chưa thấy đủ thông tin trong tài liệu đã truy xuất để khẳng định công ty có chính sách về du hành liên sao. Nếu bạn muốn, mình có thể tiếp tục rà theo một tên chính sách, phòng ban, hoặc nguồn tài liệu cụ thể hơn."}\n'
                        "Return ONLY one valid JSON object with no markdown, "
                        'using this schema: {"answer":"..."}.'
                    ),
                    "max_tokens": AGENT_SETTINGS.synthesizer.max_completion_tokens,
                    "metadata": {
                        "phase": "synthesize_answer",
                        "agent": self.name,
                        "organization_id": state.organization_id,
                        "used_verified_answer": bool(state.verified_answer),
                    },
                }
            )
            response_text = (((inference or {}).get("response") or {}).get("response_text") or "").strip()
            state.answer = self._extract_answer_text(response_text) or candidate
        except HTTPException:
            state.answer = candidate

        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        if state.answer:
            return "Da tong hop xong cau tra loi cuoi cung."
        return "Chua co du du lieu de tong hop cau tra loi cuoi cung."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "answer_length": len(state.answer),
            "used_verified_answer": bool(state.verified_answer),
        }
