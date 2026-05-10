import json
from datetime import datetime
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.agents.base import AgentWorkflowState, BaseAgent
from app.entities import database as db_entities


def _utcnow() -> datetime:
    return datetime.utcnow()


def _to_json_text(value: Any) -> str:
    return json.dumps(jsonable_encoder(value), ensure_ascii=False)


def _search_hit_summary(state: AgentWorkflowState) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for hit in state.search_hits:
        document = hit.document or {}
        summaries.append(
            {
                "document_id": hit.document_id,
                "file_name": document.get("file_name") or hit.document_id,
                "source_url": document.get("source_url") or "",
                "score": hit.score,
            }
        )
    return summaries


def _citation_summary(state: AgentWorkflowState) -> list[dict[str, Any]]:
    return [
        {
            "document_id": citation.document_id,
            "file_name": citation.file_name,
            "source_url": citation.source_url,
        }
        for citation in state.citations
    ]


def _report_artifact_summary(state: AgentWorkflowState) -> list[dict[str, Any]]:
    return [
        {
            "kind": artifact.kind,
            "label": artifact.label,
            "file_name": artifact.file_name,
            "bucket": artifact.bucket,
            "object_key": artifact.object_key,
            "source_url": artifact.source_url,
            "content_type": artifact.content_type,
        }
        for artifact in state.report_artifacts
    ]


def summarize_state(state: AgentWorkflowState) -> dict[str, Any]:
    return {
        "organization_id": state.organization_id,
        "session_id": state.session_id,
        "user_id": state.user_id,
        "question": state.question,
        "assistant_mode": state.assistant_mode,
        "feedback_context_count": len(state.feedback_contexts),
        "feedback_contexts": list(state.feedback_contexts),
        "plan_summary": state.plan_summary,
        "retrieval_queries": list(state.retrieval_queries),
        "needs_document_search": state.needs_document_search,
        "wants_report_output": state.wants_report_output,
        "report_title_hint": state.report_title_hint,
        "search_attempts": list(state.search_attempts),
        "search_hit_count": len(state.search_hits),
        "search_hits": _search_hit_summary(state),
        "citation_count": len(state.citations),
        "citations": _citation_summary(state),
        "report_artifact_count": len(state.report_artifacts),
        "report_artifacts": _report_artifact_summary(state),
        "context_count": len(state.contexts),
        "contexts": list(state.contexts),
        "draft_answer": state.draft_answer,
        "verified_answer": state.verified_answer,
        "answer": state.answer,
        "verification_notes": state.verification_notes,
        "metadata": dict(state.metadata),
    }


def create_agent_run(
    *,
    session_id: str,
    organization_id: str | None,
    user_id: str,
    question: str,
    metadata: dict[str, Any],
    db: Session,
) -> db_entities.AgentRun:
    run = db_entities.AgentRun(
        session_id=session_id,
        organization_id=organization_id,
        user_id=user_id,
        question=question,
        metadata_json=_to_json_text(metadata),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def save_agent_step(
    *,
    run_id: str,
    step_order: int,
    agent: BaseAgent,
    status: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    metadata: dict[str, Any],
    started_at: datetime,
    finished_at: datetime,
    error_message: str | None,
    db: Session,
) -> db_entities.AgentStep:
    step = db_entities.AgentStep(
        run_id=run_id,
        step_order=step_order,
        agent_name=agent.name,
        phase=agent.stage,
        status=status,
        input_json=_to_json_text(input_payload),
        output_json=_to_json_text(output_payload),
        metadata_json=_to_json_text(metadata),
        error_message=error_message,
        latency_ms=max(0, int((finished_at - started_at).total_seconds() * 1000)),
        started_at=started_at,
        finished_at=finished_at,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def complete_agent_run(
    *,
    run: db_entities.AgentRun,
    final_answer: str,
    retry_count: int,
    metadata: dict[str, Any],
    db: Session,
) -> db_entities.AgentRun:
    finished_at = _utcnow()
    run.final_answer = final_answer
    run.status = "completed"
    run.retry_count = max(0, retry_count)
    run.finished_at = finished_at
    run.total_latency_ms = max(0, int((finished_at - run.started_at).total_seconds() * 1000))
    run.metadata_json = _to_json_text(metadata)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def fail_agent_run(
    *,
    run: db_entities.AgentRun,
    error_message: str,
    metadata: dict[str, Any],
    db: Session,
) -> db_entities.AgentRun:
    finished_at = _utcnow()
    run.status = "failed"
    run.finished_at = finished_at
    run.total_latency_ms = max(0, int((finished_at - run.started_at).total_seconds() * 1000))
    payload = dict(metadata)
    payload["error_message"] = error_message
    run.metadata_json = _to_json_text(payload)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run
