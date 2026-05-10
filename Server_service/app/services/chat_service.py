import json
import time

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import messages, models
from app.dtos import chat_dto
from app.entities import database as db_entities
from app.repositories import chat_repository
from app.repositories.common import parse_json_dict, parse_json_list
from app.config import AGENT_SETTINGS
from app.services.agent_orchestrator_service import AgentOrchestratorService
from app.services.chat_artifacts import extract_report_artifacts


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_membership(self, org_id: str, user_id: str) -> db_entities.OrganizationMember | None:
        return (
            self.db.query(db_entities.OrganizationMember)
            .filter(
                db_entities.OrganizationMember.organization_id == org_id,
                db_entities.OrganizationMember.user_id == user_id,
                db_entities.OrganizationMember.status == "active",
            )
            .first()
        )

    def _require_permission(self, org_id: str, user_id: str, permission: str) -> db_entities.OrganizationMember:
        membership = self._get_membership(org_id, user_id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
        permissions = parse_json_list(membership.permissions)
        if membership.role != "admin" and permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
        return membership

    def _personal_suggestions(self) -> list[str]:
        return [
            "Tom tat lich su chat ca nhan cua toi.",
            "Goi y cach tao to chuc moi va moi thanh vien.",
            "Toi nen bat dau voi workspace nao de quan ly tai lieu?",
        ]

    def _default_organization_suggestions(self) -> list[str]:
        return [
            "Thu nhap va phuc loi hien tai gom nhung gi?",
            "Chinh sach nghi phep ap dung ra sao?",
            "Quy trinh noi bo nao lien quan den nhan vien moi?",
        ]

    def _organization_suggestions(self, org_id: str) -> list[str]:
        org = self.db.get(db_entities.Organization, org_id)
        settings = parse_json_dict(org.settings_json if org else "{}")
        configured = settings.get("suggested_questions")
        if isinstance(configured, list):
            suggestions = [str(item).strip() for item in configured if str(item).strip()]
            if suggestions:
                return suggestions[:3]
        return self._default_organization_suggestions()

    def _get_or_create_session(self, org_id: str | None, payload: models.ChatAsk) -> db_entities.ChatSession:
        if payload.session_id:
            session = chat_repository.get_chat_session(payload.session_id, self.db)
            if not session:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.SESSION_NOT_FOUND)
            if session.user_id != payload.user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc dung chat cua user khac.")
            if org_id and session.organization_id != org_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.ORGANIZATION_SESSION_MISMATCH)
            if org_id is None and session.organization_id is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session khong thuoc workspace ca nhan.")
            return session

        return chat_repository.create_chat_session(
            org_id=org_id,
            user_id=payload.user_id,
            context_type="organization" if org_id else "personal",
            title=payload.question[:80],
            db=self.db,
        )

    def _get_session_or_404(self, session_id: str) -> db_entities.ChatSession:
        session = chat_repository.get_chat_session(session_id, self.db)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.SESSION_NOT_FOUND)
        return session

    def _to_history_payload(self, session_id: str) -> list[dict]:
        history_limit = max(20, AGENT_SETTINGS.planner.history_limit, AGENT_SETTINGS.questioner.history_limit)
        history_payload: list[dict] = []
        for item in chat_repository.list_chat_history(session_id, self.db, limit=history_limit):
            cleaned_content, _artifacts = extract_report_artifacts(item.content)
            if not cleaned_content:
                continue
            history_payload.append(
                {
                    "role": "assistant" if item.sender_type != "user" else "user",
                    "content": cleaned_content,
                }
            )
        return history_payload

    def _to_feedback_contexts(self, session_id: str) -> list[dict]:
        rows = chat_repository.list_chat_feedback_history(
            session_id,
            self.db,
            limit=AGENT_SETTINGS.feedback.history_limit,
        )
        feedback_contexts: list[dict] = []
        for feedback, message in rows:
            comment = (feedback.comment or "").strip()[: AGENT_SETTINGS.feedback.comment_char_limit]
            cleaned_content, _artifacts = extract_report_artifacts(message.content)
            answer_excerpt = cleaned_content[: AGENT_SETTINGS.feedback.answer_char_limit]
            feedback_contexts.append(
                {
                    "message_id": message.id,
                    "feedback_id": feedback.id,
                    "rating": feedback.rating,
                    "comment": comment,
                    "assistant_answer_excerpt": answer_excerpt,
                    "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
                }
            )
        return feedback_contexts

    def _stream_event(self, event_type: str, **payload) -> str:
        return json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n"

    def _stream_answer_chunks(self, answer: str):
        for index in range(0, len(answer), 48):
            yield answer[index:index + 48]

    def _run_agent_workflow(self, org_id: str | None, payload: models.ChatAsk, session: db_entities.ChatSession):
        orchestrator = AgentOrchestratorService(self.db)
        return orchestrator.run(
            org_id=org_id,
            session_id=session.id,
            user_id=payload.user_id,
            question=payload.question,
            history=self._to_history_payload(session.id),
            feedback_contexts=self._to_feedback_contexts(session.id),
        )

    def chat_suggestions(self, org_id: str, acting_user_id: str) -> list[str]:
        self._require_permission(org_id, acting_user_id, "chat_advisory")
        return self._organization_suggestions(org_id)

    def personal_chat_suggestions(self, acting_user_id: str) -> list[str]:
        return self._personal_suggestions()

    def _get_public_chat_settings(self, org_id: str) -> tuple[db_entities.Organization, dict]:
        org = self.db.get(db_entities.Organization, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)
        settings = parse_json_dict(org.settings_json)
        return org, settings

    def public_chat_suggestions(self, org_id: str) -> list[str]:
        _org, settings = self._get_public_chat_settings(org_id)
        if settings.get("allow_guest_chat") is not True:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="To chuc chua mo chat cong khai.")
        return self._organization_suggestions(org_id)

    def public_ask_chat(self, org_id: str, question: str) -> dict:
        org, settings = self._get_public_chat_settings(org_id)
        if settings.get("allow_guest_chat") is not True:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="To chuc chua mo chat cong khai.")

        if settings.get("allow_guest_document_access") is not True:
            answer = (
                f"{org.name}: {org.description or 'To chuc nay da mo chat cong khai, nhung khach khong duoc dung tai lieu noi bo.'} "
                "Ban co the xem trang cong khai hoac gui yeu cau tham gia de duoc cap quyen sau."
            )
            return {
                "answer": answer,
                "citations": [],
                "guest_document_access": False,
            }

        state = AgentOrchestratorService(self.db).run_ephemeral(
            org_id=org_id,
            session_id=f"public-{org_id}",
            user_id=f"guest:{org_id}",
            question=question,
            history=[],
            feedback_contexts=[],
        )
        return {
            "answer": state.answer,
            "citations": [
                {
                    "document_id": citation.document_id,
                    "file_name": citation.file_name,
                    "source_url": citation.source_url,
                }
                for citation in state.citations
            ],
            "guest_document_access": True,
        }

    def list_chat_sessions(self, org_id: str, acting_user_id: str) -> list[db_entities.ChatSession]:
        self._require_permission(org_id, acting_user_id, "chat_advisory")
        return chat_repository.list_chat_sessions(org_id, acting_user_id, self.db)

    def list_personal_chat_sessions(self, acting_user_id: str) -> list[db_entities.ChatSession]:
        return chat_repository.list_personal_chat_sessions(acting_user_id, self.db)

    def create_chat_session(self, org_id: str, payload: models.ChatSessionCreate) -> db_entities.ChatSession:
        self._require_permission(org_id, payload.user_id, "chat_advisory")
        return chat_repository.create_chat_session(org_id, payload.user_id, payload.context_type, payload.title, self.db)

    def list_chat_messages(self, session_id: str, acting_user_id: str) -> list[db_entities.ChatMessage]:
        session = self._get_session_or_404(session_id)
        if session.organization_id:
            self._require_permission(session.organization_id, acting_user_id, "chat_advisory")
        elif session.user_id != acting_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc xem chat cua user khac.")
        return chat_repository.list_chat_messages(session_id, self.db)

    def ask_chat(self, org_id: str, payload: models.ChatAsk):
        self._require_permission(org_id, payload.user_id, "chat_advisory")
        session = self._get_or_create_session(org_id, payload)
        state = self._run_agent_workflow(org_id, payload, session)
        return chat_repository.save_chat_answer(
            session,
            payload.question,
            state.answer,
            state.citations,
            state.search_hits,
            state.report_artifacts,
            self.db,
        )

    def ask_personal_chat(self, payload: models.ChatAsk):
        session = self._get_or_create_session(None, payload)
        state = self._run_agent_workflow(None, payload, session)
        return chat_repository.save_chat_answer(
            session,
            payload.question,
            state.answer,
            state.citations,
            state.search_hits,
            state.report_artifacts,
            self.db,
        )

    def stream_chat(self, org_id: str, payload: models.ChatAsk) -> StreamingResponse:
        def event_stream():
            try:
                self._require_permission(org_id, payload.user_id, "chat_advisory")
                session = self._get_or_create_session(org_id, payload)
                yield self._stream_event("session", session=jsonable_encoder(chat_dto.to_chat_session_model(session)))
                orchestrator = AgentOrchestratorService(self.db)
                workflow = orchestrator.iter_run(
                    org_id=org_id,
                    session_id=session.id,
                    user_id=payload.user_id,
                    question=payload.question,
                    history=self._to_history_payload(session.id),
                    feedback_contexts=self._to_feedback_contexts(session.id),
                )
                while True:
                    try:
                        event = next(workflow)
                    except StopIteration as stop:
                        state = stop.value
                        break
                    yield self._stream_event(
                        event.event_type,
                        stage=event.stage,
                        agent=event.agent,
                        message=event.message,
                        **event.payload,
                    )

                for chunk in self._stream_answer_chunks(state.answer):
                    yield self._stream_event("answer_chunk", chunk=chunk)
                    time.sleep(0.01)
                result = chat_repository.save_chat_answer(
                    session,
                    payload.question,
                    state.answer,
                    state.citations,
                    state.search_hits,
                    state.report_artifacts,
                    self.db,
                )
                yield self._stream_event("complete", response=jsonable_encoder(chat_dto.to_chat_answer_model(result)))
            except HTTPException:
                yield self._stream_event("error", message="Khong the xu ly cau hoi luc nay.")
            except Exception:
                yield self._stream_event("error", message="Khong the xu ly cau hoi luc nay.")

        return StreamingResponse(
            event_stream(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    def stream_personal_chat(self, payload: models.ChatAsk) -> StreamingResponse:
        def event_stream():
            try:
                session = self._get_or_create_session(None, payload)
                yield self._stream_event("session", session=jsonable_encoder(chat_dto.to_chat_session_model(session)))
                orchestrator = AgentOrchestratorService(self.db)
                workflow = orchestrator.iter_run(
                    org_id=None,
                    session_id=session.id,
                    user_id=payload.user_id,
                    question=payload.question,
                    history=self._to_history_payload(session.id),
                    feedback_contexts=self._to_feedback_contexts(session.id),
                )
                while True:
                    try:
                        event = next(workflow)
                    except StopIteration as stop:
                        state = stop.value
                        break
                    yield self._stream_event(
                        event.event_type,
                        stage=event.stage,
                        agent=event.agent,
                        message=event.message,
                        **event.payload,
                    )

                for chunk in self._stream_answer_chunks(state.answer):
                    yield self._stream_event("answer_chunk", chunk=chunk)
                    time.sleep(0.01)
                result = chat_repository.save_chat_answer(
                    session,
                    payload.question,
                    state.answer,
                    state.citations,
                    state.search_hits,
                    state.report_artifacts,
                    self.db,
                )
                yield self._stream_event("complete", response=jsonable_encoder(chat_dto.to_chat_answer_model(result)))
            except HTTPException:
                yield self._stream_event("error", message="Khong the xu ly cau hoi luc nay.")
            except Exception:
                yield self._stream_event("error", message="Khong the xu ly cau hoi luc nay.")

        return StreamingResponse(
            event_stream(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    def create_feedback(self, message_id: str, payload: models.FeedbackCreate) -> db_entities.ChatFeedback:
        message = self.db.get(db_entities.ChatMessage, message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message khong ton tai.")
        session = self._get_session_or_404(message.session_id)
        if session.organization_id:
            self._require_permission(session.organization_id, payload.user_id, "chat_advisory")
        elif session.user_id != payload.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc gui feedback cho chat cua user khac.")
        return chat_repository.create_feedback(message_id, payload.user_id, payload.rating, payload.comment, self.db)

    def delete_chat_session(self, session_id: str, acting_user_id: str) -> None:
        session = self._get_session_or_404(session_id)
        if session.organization_id:
            self._require_permission(session.organization_id, acting_user_id, "delete_chat_sessions")
        elif session.user_id != acting_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc xoa chat cua user khac.")
        chat_repository.delete_chat_session(session, self.db)
