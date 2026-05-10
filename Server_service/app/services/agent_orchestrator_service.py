from collections.abc import Generator
from datetime import datetime

from sqlalchemy.orm import Session

from app.agents import (
    AgentWorkflowEvent,
    AgentWorkflowState,
    AnswerAgent,
    PlannerAgent,
    RetrieverAgent,
    SearchQuestionAgent,
    SynthesizerAgent,
    VerifierAgent,
)
from app.config import AGENT_SETTINGS
from app.entities.chat import CitationEntity
from app.repositories import agent_trace_repository
from app.services.report_export_service import ReportExportService


class AgentOrchestratorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.planner = PlannerAgent()
        self.questioner = SearchQuestionAgent()
        self.retriever = RetrieverAgent(db)
        self.answerer = AnswerAgent()
        self.verifier = VerifierAgent()
        self.synthesizer = SynthesizerAgent()
        self.report_exporter = ReportExportService()
        self._step_order = 0

    def _utcnow(self) -> datetime:
        return datetime.utcnow()

    def _build_run_metadata(self, state: AgentWorkflowState) -> dict:
        return {
            "organization_id": state.organization_id,
            "session_id": state.session_id,
            "user_id": state.user_id,
            "question": state.question,
            "assistant_mode": state.assistant_mode,
        }

    def _build_completion_metadata(self, state: AgentWorkflowState) -> dict:
        payload = agent_trace_repository.summarize_state(state)
        payload["retry_count"] = max(0, len(state.search_attempts) - 1)
        return payload

    def _export_report_if_needed(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if not state.wants_report_output or not state.answer:
            return state
        try:
            artifact = self.report_exporter.export_pdf_report(state)
        except Exception as exc:
            state.metadata["report_export_status"] = "failed"
            state.metadata["report_export_error"] = str(exc)
            return state

        if artifact:
            state.report_artifacts = [artifact]
            state.metadata["report_export_status"] = "completed"
            state.metadata["report_file_name"] = artifact.file_name
        else:
            state.metadata["report_export_status"] = "skipped"
        return state

    def _create_run(self, state: AgentWorkflowState):
        run = agent_trace_repository.create_agent_run(
            session_id=state.session_id,
            organization_id=state.organization_id,
            user_id=state.user_id,
            question=state.question,
            metadata=self._build_run_metadata(state),
            db=self.db,
        )
        state.metadata["agent_run_id"] = run.id
        return run

    def _run_step(self, agent, state: AgentWorkflowState, run_id: str) -> AgentWorkflowState:
        self._step_order += 1
        started_at = self._utcnow()
        input_payload = agent_trace_repository.summarize_state(state)
        try:
            state = agent.run(state)
            finished_at = self._utcnow()
            agent_trace_repository.save_agent_step(
                run_id=run_id,
                step_order=self._step_order,
                agent=agent,
                status="completed",
                input_payload=input_payload,
                output_payload=agent_trace_repository.summarize_state(state),
                metadata=agent.build_payload(state),
                started_at=started_at,
                finished_at=finished_at,
                error_message=None,
                db=self.db,
            )
            return state
        except Exception as exc:
            finished_at = self._utcnow()
            agent_trace_repository.save_agent_step(
                run_id=run_id,
                step_order=self._step_order,
                agent=agent,
                status="failed",
                input_payload=input_payload,
                output_payload=agent_trace_repository.summarize_state(state),
                metadata=agent.build_payload(state),
                started_at=started_at,
                finished_at=finished_at,
                error_message=str(exc),
                db=self.db,
            )
            raise

    def _build_state(
        self,
        *,
        org_id: str | None,
        session_id: str,
        user_id: str,
        question: str,
        history: list[dict],
        feedback_contexts: list[dict],
        assistant_mode: str,
        initial_contexts: list[dict],
    ) -> AgentWorkflowState:
        return AgentWorkflowState(
            organization_id=org_id,
            session_id=session_id,
            user_id=user_id,
            question=question,
            history=history,
            feedback_contexts=feedback_contexts,
            assistant_mode=assistant_mode,
            contexts=list(initial_contexts),
        )

    def _fallback_answer(self, state: AgentWorkflowState) -> tuple[str, list[CitationEntity]]:
        citations = state.citations
        if citations:
            file_names = ", ".join([item.file_name for item in citations])
            answerer_failure_reason = str(state.metadata.get("answerer_failure_reason") or "").strip()

            if not state.contexts:
                return (
                    "Mình đã tìm thấy ngữ cảnh liên quan, nhưng hiện chưa trích xuất được đủ nội dung để tạo câu trả lời trực tiếp. "
                    f"Các tài liệu đã tìm thấy gồm: {file_names}. Bạn có thể mở các nguồn này để đối chiếu, hoặc mình có thể giúp kiểm tra lại pipeline trích xuất nội dung."
                ), citations

            if answerer_failure_reason in {"model_inference_http_error", "empty_model_output"}:
                return (
                    "Mình đã tìm thấy ngữ cảnh liên quan và đã lấy được dữ kiện cần thiết, nhưng bước tổng hợp câu trả lời từ mô hình chưa thành công. "
                    f"Các tài liệu đã tìm thấy gồm: {file_names}. Bạn có thể thử hỏi lại, hoặc mình có thể giúp kiểm tra cấu hình Model Service và policy `chat_multi_agent`."
                ), citations

            answer = (
                "Mình đã tìm thấy các nguồn và dữ kiện liên quan nhất cho câu hỏi của bạn. "
                f"Các tài liệu đã tìm thấy gồm: {file_names}. "
                "Bạn có thể mở các nguồn này để đối chiếu nội dung gốc."
            )
            return answer, citations
        if state.organization_id:
            return "Chưa tìm thấy dữ kiện phù hợp trong kho tri thức nội bộ cho câu hỏi này.", []
        return (
            "Workspace cá nhân hiện hoạt động như trợ lý hướng dẫn sử dụng hệ thống. "
            "Mình có thể giúp bạn chọn workspace phù hợp, giải thích quyền truy cập, hoặc chỉ đường tới khu vực cần thao tác. "
            "Nếu bạn cần hỏi theo tài liệu nội bộ, hãy chuyển sang workspace tổ chức tương ứng."
        ), []

    def _apply_fallback(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if state.answer:
            return state
        answer, citations = self._fallback_answer(state)
        state.answer = answer
        state.citations = citations
        return state

    def _run_retrieval_loop(self, state: AgentWorkflowState) -> AgentWorkflowState:
        if not state.organization_id or not state.needs_document_search:
            return state

        total_attempts = AGENT_SETTINGS.retrieval.no_hit_retries + 1
        for _ in range(total_attempts):
            run_id = state.metadata["agent_run_id"]
            state = self._run_step(self.questioner, state, run_id)
            state = self._run_step(self.retriever, state, run_id)
            if state.search_hits:
                break
        return state

    def run(
        self,
        *,
        org_id: str | None,
        session_id: str,
        user_id: str,
        question: str,
        history: list[dict],
        feedback_contexts: list[dict],
        assistant_mode: str = "organization_rag",
        initial_contexts: list[dict] | None = None,
    ) -> AgentWorkflowState:
        self._step_order = 0
        state = self._build_state(
            org_id=org_id,
            session_id=session_id,
            user_id=user_id,
            question=question,
            history=history,
            feedback_contexts=feedback_contexts,
            assistant_mode=assistant_mode,
            initial_contexts=initial_contexts or [],
        )
        run = self._create_run(state)
        try:
            state = self._run_step(self.planner, state, run.id)
            state = self._run_retrieval_loop(state)
            state = self._run_step(self.answerer, state, run.id)
            state = self._run_step(self.verifier, state, run.id)
            state = self._run_step(self.synthesizer, state, run.id)
            state = self._export_report_if_needed(state)
            state = self._apply_fallback(state)
            agent_trace_repository.complete_agent_run(
                run=run,
                final_answer=state.answer,
                retry_count=max(0, len(state.search_attempts) - 1),
                metadata=self._build_completion_metadata(state),
                db=self.db,
            )
            return state
        except Exception as exc:
            agent_trace_repository.fail_agent_run(
                run=run,
                error_message=str(exc),
                metadata=self._build_completion_metadata(state),
                db=self.db,
            )
            raise

    def iter_run(
        self,
        *,
        org_id: str | None,
        session_id: str,
        user_id: str,
        question: str,
        history: list[dict],
        feedback_contexts: list[dict],
        assistant_mode: str = "organization_rag",
        initial_contexts: list[dict] | None = None,
    ) -> Generator[AgentWorkflowEvent, None, AgentWorkflowState]:
        self._step_order = 0
        state = self._build_state(
            org_id=org_id,
            session_id=session_id,
            user_id=user_id,
            question=question,
            history=history,
            feedback_contexts=feedback_contexts,
            assistant_mode=assistant_mode,
            initial_contexts=initial_contexts or [],
        )
        run = self._create_run(state)
        try:
            yield self.planner.start_event()
            state = self._run_step(self.planner, state, run.id)
            yield self.planner.finish_event(state)

            if state.organization_id and state.needs_document_search:
                total_attempts = AGENT_SETTINGS.retrieval.no_hit_retries + 1
                for attempt_index in range(total_attempts):
                    yield self.questioner.start_event()
                    state = self._run_step(self.questioner, state, run.id)
                    yield self.questioner.finish_event(state)

                    yield self.retriever.start_event()
                    state = self._run_step(self.retriever, state, run.id)
                    yield self.retriever.finish_event(state)
                    for event in self.retriever.extra_events(state):
                        yield event
                    if state.search_hits:
                        break
                    if attempt_index < total_attempts - 1:
                        yield AgentWorkflowEvent(
                        event_type="status",
                        stage="retrieval_retry",
                        agent="orchestrator",
                        message="Chưa tìm thấy tài liệu phù hợp, đang thử một bộ truy vấn khác.",
                        payload={"attempt": attempt_index + 1, "remaining_retries": total_attempts - attempt_index - 1},
                    )
            else:
                yield self.retriever.start_event()
                state = self._run_step(self.retriever, state, run.id)
                yield self.retriever.finish_event(state)

            yield self.answerer.start_event()
            state = self._run_step(self.answerer, state, run.id)
            yield self.answerer.finish_event(state)

            yield self.verifier.start_event()
            state = self._run_step(self.verifier, state, run.id)
            yield self.verifier.finish_event(state)

            yield self.synthesizer.start_event()
            state = self._run_step(self.synthesizer, state, run.id)
            yield self.synthesizer.finish_event(state)

            if state.wants_report_output:
                yield AgentWorkflowEvent(
                    event_type="status",
                    stage="report_export",
                    agent="report_exporter",
                    message="Đang xuất báo cáo PDF để bạn có thể mở trực tiếp.",
                )
            state = self._export_report_if_needed(state)
            if state.wants_report_output:
                message = (
                    "Đã tạo xong báo cáo PDF đính kèm trong câu trả lời."
                    if state.report_artifacts
                    else "Chưa tạo được file PDF, nhưng nội dung markdown của báo cáo vẫn sẵn sàng."
                )
                yield AgentWorkflowEvent(
                    event_type="status",
                    stage="report_export",
                    agent="report_exporter",
                    message=message,
                    payload={"artifact_count": len(state.report_artifacts)},
                )
            state = self._apply_fallback(state)
            agent_trace_repository.complete_agent_run(
                run=run,
                final_answer=state.answer,
                retry_count=max(0, len(state.search_attempts) - 1),
                metadata=self._build_completion_metadata(state),
                db=self.db,
            )
            return state
        except Exception as exc:
            agent_trace_repository.fail_agent_run(
                run=run,
                error_message=str(exc),
                metadata=self._build_completion_metadata(state),
                db=self.db,
            )
            raise
