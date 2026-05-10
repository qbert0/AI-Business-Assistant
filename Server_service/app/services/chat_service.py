import json
import time

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app import messages, models
from app.dtos import chat_dto
from app.entities import database as db_entities
from app.repositories import chat_repository
from app.repositories.common import parse_json_list
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
            "Neu toi muon chat theo tai lieu noi bo thi nen vao workspace nao?",
            "Toi muon upload tai lieu cho to chuc thi can vao dau?",
            "Role admin va user trong he thong khac nhau nhu the nao?",
        ]

    def _organization_suggestions(self) -> list[str]:
        return [
            "Thu nhap va phuc loi hien tai gom nhung gi?",
            "Chinh sach nghi phep ap dung ra sao?",
            "Quy trinh noi bo nao lien quan den nhan vien moi?",
        ]

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

    def _build_personal_guide_contexts(self, user_id: str) -> list[dict]:
        user = self.db.get(db_entities.User, user_id)
        memberships = (
            self.db.query(db_entities.OrganizationMember)
            .options(joinedload(db_entities.OrganizationMember.organization))
            .filter(
                db_entities.OrganizationMember.user_id == user_id,
                db_entities.OrganizationMember.status == "active",
            )
            .order_by(db_entities.OrganizationMember.joined_at.asc())
            .all()
        )

        organization_lines: list[str] = []
        chat_ready_orgs: list[str] = []
        upload_ready_orgs: list[str] = []
        default_org_name = ""

        for membership in memberships:
            organization = membership.organization
            organization_name = organization.name if organization else membership.organization_id
            permissions = parse_json_list(membership.permissions)
            permission_summary = ", ".join(permissions) if permissions else "khong co permission rieng"
            organization_lines.append(
                f"- {organization_name}: role {membership.role}; quyen {permission_summary}."
            )
            if membership.role == "admin" or "chat_advisory" in permissions:
                chat_ready_orgs.append(organization_name)
            if membership.role == "admin" or "upload_documents" in permissions:
                upload_ready_orgs.append(organization_name)
            if user and user.default_organization_id and membership.organization_id == user.default_organization_id:
                default_org_name = organization_name

        if organization_lines:
            workspace_access_summary = "\n".join(
                [
                    f"User hien tai: {user.full_name if user else user_id}.",
                    f"So workspace to chuc dang active: {len(organization_lines)}.",
                    "Danh sach workspace co the truy cap:",
                    *organization_lines,
                    (
                        f"Workspace mac dinh hien tai: {default_org_name}."
                        if default_org_name
                        else "User chua dat workspace mac dinh."
                    ),
                    (
                        f"Co the vao cac workspace sau de chat theo tai lieu: {', '.join(chat_ready_orgs)}."
                        if chat_ready_orgs
                        else "Hien chua co workspace nao san sang cho chat theo tai lieu."
                    ),
                    (
                        f"Co the vao cac workspace sau de upload/quan ly tai lieu: {', '.join(upload_ready_orgs)}."
                        if upload_ready_orgs
                        else "Hien chua co workspace nao ma user co quyen upload tai lieu."
                    ),
                ]
            )
        else:
            workspace_access_summary = "\n".join(
                [
                    f"User hien tai: {user.full_name if user else user_id}.",
                    "User chua tham gia workspace to chuc nao o trang thai active.",
                    "Neu user hoi ve tai lieu noi bo, can giai thich rang ho can tao to chuc moi hoac tham gia mot to chuc truoc.",
                ]
            )

        return [
            {
                "title": "Vai tro cua workspace ca nhan",
                "content": (
                    "Workspace ca nhan la tro ly huong dan su dung he thong. "
                    "No khong truy xuat Elasticsearch, khong doc tai lieu noi bo, va khong duoc khang dinh noi dung chinh sach/doanh thu/quy trinh cua to chuc nhu the retrieval chat. "
                    "Dung no de giai thich tinh nang, role, permission, luong thao tac, va chi nguoi dung den dung workspace."
                ),
                "source": "system://personal-workspace-role",
                "metadata": {"kind": "system_guide"},
            },
            {
                "title": "Cau truc san pham va luong thao tac",
                "content": (
                    "Cac khu vuc chinh cua he thong gom: Ca nhan, Tong quan to chuc, Workspace chat theo to chuc, Nhan vien, Tai lieu, Pipeline, Phan tich, Cai dat. "
                    "Luot thao tac thuong gap: tao to chuc moi hoac tham gia to chuc; admin upload tai lieu trong muc Tai lieu; he thong chunking/embedding/index; "
                    "sau do user vao workspace to chuc de chat theo tai lieu da index. "
                    "Neu user can quan ly nhan vien hoac cai dat to chuc, ho thuong can vao workspace to chuc va co role admin hoac permission phu hop."
                ),
                "source": "system://product-navigation",
                "metadata": {"kind": "system_guide"},
            },
            {
                "title": "Role va permission co ban",
                "content": (
                    "Role admin o cap to chuc thuong co toan bo quyen quan tri trong to chuc do, bao gom access_org_settings, upload_documents, view_employees, view_analytics, "
                    "edit_sensitive_restrictions, delete_chat_sessions, chat_advisory va read_documents. "
                    "Role user thuong duoc cap mot tap quyen hep hon, pho bien la chat_advisory va read_documents. "
                    "Khi huong dan nguoi dung, nen noi ro ho can vao workspace nao va can quyen nao de thuc hien thao tac."
                ),
                "source": "system://roles-and-permissions",
                "metadata": {"kind": "system_guide"},
            },
            {
                "title": "Ngu canh truy cap hien tai cua user",
                "content": workspace_access_summary,
                "source": "system://user-workspace-access",
                "metadata": {"kind": "user_scope"},
            },
        ]

    def _stream_event(self, event_type: str, **payload) -> str:
        return json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n"

    def _stream_answer_chunks(self, answer: str):
        for index in range(0, len(answer), 48):
            yield answer[index:index + 48]

    def _run_agent_workflow(self, org_id: str | None, payload: models.ChatAsk, session: db_entities.ChatSession):
        orchestrator = AgentOrchestratorService(self.db)
        assistant_mode = "organization_rag" if org_id else "personal_system_guide"
        initial_contexts = self._build_personal_guide_contexts(payload.user_id) if org_id is None else []
        return orchestrator.run(
            org_id=org_id,
            session_id=session.id,
            user_id=payload.user_id,
            question=payload.question,
            history=self._to_history_payload(session.id),
            feedback_contexts=self._to_feedback_contexts(session.id),
            assistant_mode=assistant_mode,
            initial_contexts=initial_contexts,
        )

    def chat_suggestions(self, org_id: str, acting_user_id: str) -> list[str]:
        self._require_permission(org_id, acting_user_id, "chat_advisory")
        return self._organization_suggestions()

    def personal_chat_suggestions(self, acting_user_id: str) -> list[str]:
        return self._personal_suggestions()

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
                    assistant_mode="organization_rag",
                    initial_contexts=[],
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
                    assistant_mode="personal_system_guide",
                    initial_contexts=self._build_personal_guide_contexts(payload.user_id),
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
