import re

from fastapi import HTTPException

from app.agents.base import BaseAgent, AgentWorkflowState, clean_text, format_feedback_guidance, parse_json_object
from app.config import AGENT_SETTINGS
from app.services.model_service import create_inference


class SynthesizerAgent(BaseAgent):
    name = "synthesizer"
    stage = "synthesizing"
    start_message = "Đang hoàn thiện câu trả lời cuối cùng."
    METRIC_LINE_PATTERN = re.compile(
        r"^\s*(?:[-*]\s*)?[^:\n]{2,64}:\s*[\d.,\s\u202f]+(?:VNĐ|%|ty|tỷ|blocks?)?\s*$",
        flags=re.IGNORECASE,
    )

    def _extract_answer_text(self, response_text: str) -> str:
        payload = parse_json_object(response_text)
        if payload:
            answer = clean_text(payload.get("answer"))
            if answer:
                return answer
        return response_text.strip()

    def _build_compact_contexts(self, state: AgentWorkflowState) -> list[dict]:
        compact_contexts: list[dict] = []
        for item in state.contexts[: AGENT_SETTINGS.synthesizer.context_item_limit]:
            compact_contexts.append(
                {
                    **item,
                    "content": (item.get("content") or "")[: AGENT_SETTINGS.synthesizer.context_char_limit],
                }
            )
        return compact_contexts

    def _looks_like_insufficient_answer(self, text: str) -> bool:
        lowered = clean_text(text).lower()
        return any(
            phrase in lowered
            for phrase in (
                "chưa tìm thấy dữ liệu",
                "chưa thấy đủ thông tin",
                "chưa có đủ thông tin",
                "không đủ thông tin",
                "không tìm thấy dữ liệu",
                "insufficient information",
                "not enough information",
            )
        )

    def _numeric_tokens(self, text: str) -> list[str]:
        return re.findall(r"\d[\d.,]*", clean_text(text))

    def _extract_chart_blocks(self, text: str) -> list[str]:
        return re.findall(r"```chart\s*\n.*?\n```", text or "", flags=re.DOTALL)

    def _contains_chart_block(self, text: str) -> bool:
        return bool(self._extract_chart_blocks(text))

    def _contains_ascii_chart(self, text: str) -> bool:
        cleaned = text or ""
        return "█" in cleaned or bool(re.search(r"(?im)^\s*(bar|line|pie)\s+chart\b", cleaned))

    def _contains_markdown_table(self, text: str) -> bool:
        lines = (text or "").splitlines()
        for index, line in enumerate(lines[:-1]):
            if "|" in line and re.match(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+(?:\s*:?-{3,}:\s*)?\|?\s*$", lines[index + 1] or ""):
                return True
        return False

    def _merge_candidate_with_chart_blocks(self, candidate: str, synthesized: str) -> str:
        chart_blocks = list(dict.fromkeys(self._extract_chart_blocks(synthesized)))
        if not chart_blocks:
            return candidate
        return candidate.rstrip() + "\n\n" + "\n\n".join(chart_blocks)

    def _trim_visual_repetition(self, text: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned or not self._contains_chart_block(cleaned):
            return cleaned

        match = re.search(r"```chart\s*\n.*?\n```", cleaned, flags=re.DOTALL)
        if not match:
            return cleaned

        before_chart = cleaned[:match.start()].strip()
        chart_block = match.group(0)
        after_chart = cleaned[match.end():].strip()

        before_lines = [line.rstrip() for line in before_chart.splitlines()]
        metric_line_count = sum(1 for line in before_lines if self.METRIC_LINE_PATTERN.match(line.strip()))

        if metric_line_count >= 4:
            filtered_lines = []
            for line in before_lines:
                stripped = line.strip()
                if self.METRIC_LINE_PATTERN.match(stripped):
                    continue
                if "█" in stripped:
                    continue
                if re.match(r"(?i)^(bar|line|pie)\s+chart\b", stripped):
                    continue
                filtered_lines.append(line)
            before_chart = "\n".join(filtered_lines).strip()

        pieces = [piece for piece in (before_chart, chart_block, after_chart) if piece]
        normalized = "\n\n".join(pieces)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
        return normalized

    def _should_keep_candidate(
        self,
        *,
        candidate: str,
        synthesized: str,
        verification_notes: str,
    ) -> bool:
        if not candidate or not synthesized:
            return False

        notes_lower = clean_text(verification_notes).lower()
        notes_allow_insufficiency = any(
            phrase in notes_lower
            for phrase in (
                "insufficient",
                "unsupported",
                "not enough information",
                "không đủ thông tin",
                "thiếu thông tin",
            )
        )
        if (
            self._looks_like_insufficient_answer(synthesized)
            and not self._looks_like_insufficient_answer(candidate)
            and not notes_allow_insufficiency
        ):
            return True

        if (
            self._contains_chart_block(synthesized)
            and (self._contains_ascii_chart(candidate) or self._contains_markdown_table(candidate))
        ):
            return False

        candidate_numbers = list(dict.fromkeys(self._numeric_tokens(candidate)))
        if len(candidate_numbers) >= 3:
            preserved_numbers = [token for token in candidate_numbers if token in synthesized]
            if len(preserved_numbers) < 2:
                return True

        visible_synthesized = re.sub(r"```chart\s*\n.*?\n```", "", synthesized, flags=re.DOTALL).strip()
        if self._contains_chart_block(synthesized) and len(candidate) >= 120 and len(visible_synthesized) < 20:
            return True

        return False

    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        candidate = (state.verified_answer or state.draft_answer or "").strip()
        if not candidate:
            state.answer = ""
            return state

        feedback_guidance = format_feedback_guidance(state.feedback_contexts)
        report_mode_guidance = (
            "\n\nReport mode:\n"
            "- The user explicitly wants a report or PDF artifact.\n"
            f"- Produce polished Markdown that can stand alone as a report titled `{state.report_title_hint or 'Bao cao tong hop'}`.\n"
            "- Start with a single `#` top-level title.\n"
            "- Prefer a clear report structure such as `## Tóm tắt`, `## Phân tích chính`, `## Dữ liệu nổi bật`, or another grounded structure that fits the content.\n"
            "- Write in a formal, concise report tone instead of a casual chat tone.\n"
            "- Include tables or one chart only when they materially improve readability.\n"
            "- Do not add a references section in the answer body; the export pipeline will attach source information separately.\n"
            if state.wants_report_output
            else ""
        )
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
                    "system_prompt": (
                        "You are the synthesizer agent for an internal business assistant. "
                        "Rewrite the candidate answer into a polished final reply that feels complete and natural in conversation. "
                        "The final reply will be stored in the JSON field `answer` and rendered as Markdown in a chat UI, so the Markdown must be clean, stable, and easy to parse. "
                        "Treat the candidate answer as the source of truth for the final wording unless verification notes explicitly say it is unsupported or incomplete. "
                        "Keep the meaning and factual claims unchanged. "
                        "Do not add new facts, citations, unsupported details, or new limitations. "
                        "Do not remove grounded facts that already appear in the candidate answer. "
                        "If the candidate answer already contains grounded facts, preserve those facts in the final answer. "
                        "Never replace a grounded candidate answer with a generic 'not enough information' response unless the verification notes explicitly say the candidate is unsupported or missing evidence. "
                        "Prefer a fuller answer over a one-line fragment. "
                        "First answer the question directly, then add only the supporting clarification or limitation that is already justified by the candidate answer or verification notes. "
                        "Do not pad with generic filler, but do make the reply feel complete. "
                        "Use the same language as the user's question unless the user explicitly asked for another language. "
                        "\n\nMarkdown rules for the `answer` field:\n"
                        "- Use only this Markdown subset: plain paragraphs, `#`-`###` headings, `-` bullet lists, `1.` numbered lists, simple pipe tables, blockquotes, fenced code blocks, inline code, and normal Markdown links.\n"
                        "- Leave a blank line between paragraphs, headings, lists, tables, and code blocks.\n"
                        "- Keep lists flat. Do not use nested bullets, nested numbering, or multi-level indentation.\n"
                        "- Keep list items short and self-contained. Prefer one sentence per bullet when possible.\n"
                        "- Use headings only when the answer truly has multiple sections. For short factual answers, do not add a heading.\n"
                        "- If headings are needed, prefer concise titles such as `## Tóm tắt`, `## Chi tiết`, or `## Lưu ý`.\n"
                        "- Do not output raw HTML.\n"
                        "- Do not output footnotes, task lists, Mermaid, math blocks, or custom Markdown extensions.\n"
                        "- Do not output a references section or inline citations, because the application shows source links separately.\n"
                        "- Do not wrap the entire answer in a code fence.\n"
                        "- Use fenced code blocks only for literal code/text or for the special visualization block described below.\n"
                        "- Avoid tables unless they genuinely improve clarity. If you use a table, keep it simple and valid pipe-table Markdown.\n"
                        "- Newlines inside the `answer` string are allowed and encouraged when they improve readability.\n"
                        "- Never draw ASCII or Unicode pseudo-charts using characters such as `█`, `|`, `-`, or text spacing.\n"
                        "- Do not repeat the same metrics in three forms at once, such as prose + bullet list + chart, unless the user explicitly asks for all of them.\n"
                        "- If you include a chart, keep the prose concise: one direct lead sentence and at most one or two short insights.\n"
                        "- When a chart is present, do not enumerate every metric again as separate `Khoản mục: giá trị` lines unless the user explicitly asks for a full textual listing.\n"
                        "- If you include a table, do not also repeat every row again as bullets unless the user explicitly asks for both a table and bullets.\n"
                        "\nVisualization rules:\n"
                        "- If the grounded answer includes structured numeric comparisons, a trend across periods, or a small composition breakdown, you may add one supplemental chart block after the prose answer.\n"
                        "- The chart must be optional support, not a replacement for the prose answer. Always answer in prose first.\n"
                        "- Use only this exact fenced block format with info string `chart` and one valid JSON object inside.\n"
                        "- Allowed chart types: `bar`, `line`, `pie`.\n"
                        "- Every number in the chart must already be grounded in the candidate answer or trusted context. Do not invent or estimate values.\n"
                        "- Keep chart specs compact: at most 8 categories and at most 2 series.\n"
                        "- Do not output both a markdown table and a chart in the same answer unless the user explicitly asks for both.\n"
                        "- Chart JSON schema:\n"
                        "  `{\"type\":\"bar|line|pie\",\"title\":\"...\",\"xLabel\":\"...\",\"yLabel\":\"...\",\"categories\":[\"...\"],\"series\":[{\"name\":\"...\",\"data\":[1,2,3]}],\"format\":\"number|currency_vnd|percent\",\"note\":\"...\"}`\n"
                        + report_mode_guidance
                        + (f"\n\n{feedback_guidance}\nUse this feedback to improve clarity, completeness, and tone, but do not introduce any new factual claims." if feedback_guidance else "")
                        + "\n"
                        "Examples:\n"
                        'Question: "Thông tư về thời hạn bảo quản tài liệu được ban hành vào ngày bao nhiêu?"\n'
                        'Candidate answer: "19 tháng 12 năm 2022."\n'
                        'Verification notes: "The document header shows the issuance date."\n'
                        'Output: {"answer":"Thông tư được ban hành vào ngày 19 tháng 12 năm 2022. Thông tin này xuất hiện ngay ở phần đầu văn bản, tại dòng ghi ngày ban hành của thông tư."}\n'
                        'Question: "Hồ sơ gốc được bảo quản bao lâu?"\n'
                        'Candidate answer: "Theo Thông tư 10/2022/TT-BNV, hồ sơ gốc được bảo quản trong vòng 10 năm."\n'
                        'Verification notes: "Grounded in the retrieved regulation."\n'
                        'Output: {"answer":"### Tóm tắt\\n\\nTheo Thông tư 10/2022/TT-BNV, thời hạn bảo quản hồ sơ gốc là 10 năm.\\n\\n### Lưu ý\\n\\n- Đây là mốc được xác định theo quy định trong tài liệu đã truy xuất.\\n- Nếu bạn cần áp dụng cho một loại hồ sơ cụ thể, mình có thể đối chiếu tiếp đúng nhóm hồ sơ đó."}\n'
                        'Question: "Quy trình này gồm những bước nào?"\n'
                        'Candidate answer: "Quy trình gồm tiếp nhận hồ sơ, kiểm tra tính đầy đủ, trình phê duyệt và lưu kết quả."\n'
                        'Verification notes: "Step order confirmed from internal process note."\n'
                        'Output: {"answer":"### Các bước chính\\n\\n1. Tiếp nhận hồ sơ.\\n2. Kiểm tra tính đầy đủ của hồ sơ.\\n3. Trình phê duyệt theo quy trình nội bộ.\\n4. Lưu kết quả sau khi hoàn tất xử lý."}\n'
                        'Question: "Bạn hãy show cho tôi kết quả kinh doanh của công ty TNHH Demo Financial năm 2025 nhé."\n'
                        'Candidate answer: "Trong năm tài chính 2025, Công ty TNHH Demo Financial ghi nhận doanh thu thuần 12,500,000,000 VNĐ, lợi nhuận gộp 5,300,000,000 VNĐ, chi phí vận hành 2,100,000,000 VNĐ, lợi nhuận trước thuế 3,200,000,000 VNĐ, thuế TNDN 640,000,000 VNĐ và lợi nhuận sau thuế 2,560,000,000 VNĐ. Các chỉ số chủ chốt cho thấy doanh thu tăng đều qua các quý, đặc biệt mạnh trong quý 4."\n'
                        'Verification notes: "Skipped model verification because the retrieved context was too long."\n'
                        'Output: {"answer":"### Kết quả kinh doanh năm 2025\\n\\nTrong năm tài chính 2025, Công ty TNHH Demo Financial ghi nhận doanh thu thuần 12,500,000,000 VNĐ, lợi nhuận gộp 5,300,000,000 VNĐ, chi phí vận hành 2,100,000,000 VNĐ, lợi nhuận trước thuế 3,200,000,000 VNĐ, thuế TNDN 640,000,000 VNĐ và lợi nhuận sau thuế 2,560,000,000 VNĐ.\\n\\nDoanh thu tăng đều qua các quý, trong đó quý 4 là giai đoạn tăng mạnh hơn.\\n\\n```chart\\n{\"type\":\"bar\",\"title\":\"Các chỉ số chính năm 2025\",\"xLabel\":\"Khoản mục\",\"yLabel\":\"VNĐ\",\"categories\":[\"Doanh thu thuần\",\"Lợi nhuận gộp\",\"Lợi nhuận trước thuế\",\"Lợi nhuận sau thuế\"],\"series\":[{\"name\":\"2025\",\"data\":[12500000000,5300000000,3200000000,2560000000]}],\"format\":\"currency_vnd\",\"note\":\"Biểu đồ tóm tắt các chỉ số tài chính chính đã nêu trong phần trả lời.\"}\\n```"}\n'
                        'Question: "có biểu đồ cột không?"\n'
                        'Candidate answer: "Doanh thu thuần: 12,500,000,000 VNĐ\\nGiá vốn hàng bán: 7,200,000,000 VNĐ\\nLợi nhuận gộp: 5,300,000,000 VNĐ\\n...\\nBar chart (1 block = 1,000,000,000 VNĐ):\\nDoanh thu thuần | ████████████ 12.5\\n..."\n'
                        'Verification notes: "Grounded in the retrieved financial report."\n'
                        'Output: {"answer":"Có. Dưới đây là biểu đồ cột tóm tắt các khoản mục tài chính chính năm 2025. Doanh thu thuần là chỉ số lớn nhất, còn lợi nhuận sau thuế đạt 2,560,000,000 VNĐ.\\n\\n```chart\\n{\"type\":\"bar\",\"title\":\"Các chỉ số tài chính năm 2025\",\"xLabel\":\"Khoản mục\",\"yLabel\":\"VNĐ\",\"categories\":[\"Doanh thu thuần\",\"Giá vốn hàng bán\",\"Lợi nhuận gộp\",\"Chi phí vận hành\",\"Lợi nhuận trước thuế\",\"Thuế TNDN\",\"Lợi nhuận sau thuế\"],\"series\":[{\"name\":\"2025\",\"data\":[12500000000,7200000000,5300000000,2100000000,3200000000,640000000,2560000000]}],\"format\":\"currency_vnd\",\"note\":\"Biểu đồ tóm tắt các chỉ số tài chính chính năm 2025.\"}\\n```"}\n'
                        'Question: "Công ty có chính sách du hành liên sao không?"\n'
                        'Candidate answer: "Hiện chưa có đủ thông tin trong tài liệu đã truy xuất để khẳng định công ty có chính sách này."\n'
                        'Verification notes: "Insufficient grounded evidence."\n'
                        'Output: {"answer":"Hiện mình chưa thấy đủ thông tin trong tài liệu đã truy xuất để khẳng định công ty có chính sách về du hành liên sao.\\n\\nNếu bạn muốn, mình có thể tiếp tục rà theo một tên chính sách, phòng ban, hoặc nguồn tài liệu cụ thể hơn."}\n'
                        "Return ONLY one valid JSON object with no prose outside the JSON object, "
                        'using this schema: {"answer":"..."}. The JSON object itself must not be wrapped in Markdown fences.'
                    ),
                    "external_contexts": self._build_compact_contexts(state),
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
            synthesized_answer = self._trim_visual_repetition(self._extract_answer_text(response_text))
            if self._should_keep_candidate(
                candidate=candidate,
                synthesized=synthesized_answer,
                verification_notes=state.verification_notes,
            ):
                state.answer = self._merge_candidate_with_chart_blocks(candidate, synthesized_answer)
            else:
                state.answer = synthesized_answer or candidate
        except HTTPException:
            state.answer = candidate

        return state

    def finish_message(self, state: AgentWorkflowState) -> str:
        if state.answer:
            return "Đã hoàn thiện xong câu trả lời cuối cùng."
        return "Chưa có đủ dữ liệu để hoàn thiện câu trả lời cuối cùng."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, object]:
        return {
            "answer_length": len(state.answer),
            "used_verified_answer": bool(state.verified_answer),
        }
