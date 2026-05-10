from collections.abc import Generator

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


class AgentOrchestratorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.planner = PlannerAgent()
        self.questioner = SearchQuestionAgent()
        self.retriever = RetrieverAgent(db)
        self.answerer = AnswerAgent()
        self.verifier = VerifierAgent()
        self.synthesizer = SynthesizerAgent()

    def _build_state(
        self,
        *,
        org_id: str | None,
        session_id: str,
        user_id: str,
        question: str,
        history: list[dict],
    ) -> AgentWorkflowState:
        return AgentWorkflowState(
            organization_id=org_id,
            session_id=session_id,
            user_id=user_id,
            question=question,
            history=history,
        )

    def _fallback_answer(self, state: AgentWorkflowState) -> tuple[str, list[CitationEntity]]:
        citations = state.citations
        if citations:
            answer = (
                "Toi tim thay cac tai lieu lien quan nhat trong Elasticsearch cho cau hoi cua ban: "
                + " ".join([f"- {item.file_name} ({item.source_url})" for item in citations])
                + " Ban co the mo cac nguon nay de doi chieu noi dung goc."
            )
            return answer, citations
        if state.organization_id:
            return "Chua tim thay tai lieu phu hop trong Elasticsearch cho cau hoi nay.", []
        return (
            "Workspace ca nhan hien chua gan kho tai lieu noi bo. "
            "Ban co the tao to chuc hoac chon workspace to chuc de hoi dap theo tai lieu."
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
            state = self.questioner.run(state)
            state = self.retriever.run(state)
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
    ) -> AgentWorkflowState:
        state = self._build_state(
            org_id=org_id,
            session_id=session_id,
            user_id=user_id,
            question=question,
            history=history,
        )
        state = self.planner.run(state)
        state = self._run_retrieval_loop(state)
        state = self.answerer.run(state)
        state = self.verifier.run(state)
        state = self.synthesizer.run(state)
        return self._apply_fallback(state)

    def iter_run(
        self,
        *,
        org_id: str | None,
        session_id: str,
        user_id: str,
        question: str,
        history: list[dict],
    ) -> Generator[AgentWorkflowEvent, None, AgentWorkflowState]:
        state = self._build_state(
            org_id=org_id,
            session_id=session_id,
            user_id=user_id,
            question=question,
            history=history,
        )
        yield self.planner.start_event()
        state = self.planner.run(state)
        yield self.planner.finish_event(state)

        if state.organization_id and state.needs_document_search:
            total_attempts = AGENT_SETTINGS.retrieval.no_hit_retries + 1
            for attempt_index in range(total_attempts):
                yield self.questioner.start_event()
                state = self.questioner.run(state)
                yield self.questioner.finish_event(state)

                yield self.retriever.start_event()
                state = self.retriever.run(state)
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
                        message="Chua co hit phu hop, dang thu mot bo cau hoi truy xuat khac.",
                        payload={"attempt": attempt_index + 1, "remaining_retries": total_attempts - attempt_index - 1},
                    )
        else:
            yield self.retriever.start_event()
            state = self.retriever.run(state)
            yield self.retriever.finish_event(state)

        yield self.answerer.start_event()
        state = self.answerer.run(state)
        yield self.answerer.finish_event(state)

        yield self.verifier.start_event()
        state = self.verifier.run(state)
        yield self.verifier.finish_event(state)

        yield self.synthesizer.start_event()
        state = self.synthesizer.run(state)
        yield self.synthesizer.finish_event(state)
        return self._apply_fallback(state)
