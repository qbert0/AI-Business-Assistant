import json
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import messages, models
from app.database import get_db
from app.dtos import chat_dto
from app.entities import database as db_entities
from app.entities.chat import CitationEntity
from app.entities.search import SearchHitEntity
from app.repositories import chat_repository, documents_repository
from app.repositories.common import parse_json_dict, parse_json_list
from app.services.document_preview import extract_document_text
from app.services.model_service import create_inference
from app.services.search_service import query_documents
from app.services.search_service import index_document
from app.services.storage import get_file_from_minio

router = APIRouter()


def _get_membership(org_id: str, user_id: str, db: Session) -> db_entities.OrganizationMember | None:
    return (
        db.query(db_entities.OrganizationMember)
        .filter(
            db_entities.OrganizationMember.organization_id == org_id,
            db_entities.OrganizationMember.user_id == user_id,
            db_entities.OrganizationMember.status == "active",
        )
        .first()
    )


def _require_permission(org_id: str, user_id: str, permission: str, db: Session) -> db_entities.OrganizationMember:
    membership = _get_membership(org_id, user_id, db)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
    permissions = parse_json_list(membership.permissions)
    if membership.role != "admin" and permission not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
    return membership


def _personal_suggestions() -> list[str]:
    return [
        "Tom tat lich su chat ca nhan cua toi.",
        "Goi y cach tao to chuc moi va moi thanh vien.",
        "Toi nen bat dau voi workspace nao de quan ly tai lieu?",
    ]


def _organization_suggestions() -> list[str]:
    return [
        "Thu nhap va phuc loi hien tai gom nhung gi?",
        "Chinh sach nghi phep ap dung ra sao?",
        "Quy trinh noi bo nao lien quan den nhan vien moi?",
    ]


def _get_or_create_session(org_id: str | None, payload: models.ChatAsk, db: Session) -> db_entities.ChatSession:
    if payload.session_id:
        session = chat_repository.get_chat_session(payload.session_id, db)
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
        db=db,
    )


def _get_session_or_404(session_id: str, db: Session) -> db_entities.ChatSession:
    session = chat_repository.get_chat_session(session_id, db)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.SESSION_NOT_FOUND)
    return session


def _to_history_payload(session_id: str, db: Session) -> list[dict]:
    return [
        {
            "role": "assistant" if item.sender_type != "user" else "user",
            "content": item.content,
        }
        for item in chat_repository.list_chat_history(session_id, db)
        if item.content
    ]


def _to_citations(hits: list[SearchHitEntity]) -> list[CitationEntity]:
    return [
        CitationEntity(
            document_id=hit.document.get("document_id") or hit.document_id,
            file_name=hit.document.get("file_name") or hit.document_id,
            source_url=hit.document.get("source_url") or "",
        )
        for hit in hits
    ]


def _to_context_items(hits: list[SearchHitEntity]) -> list[dict]:
    context_items: list[dict] = []
    for hit in hits:
        document = hit.document or {}
        content = document.get("content_text") or ""
        if not content:
            metadata = document.get("metadata") or {}
            content = metadata.get("content_text") or metadata.get("preview_text") or ""
        if not content:
            continue
        context_items.append(
            {
                "title": document.get("file_name") or hit.document_id,
                "content": content[:8000],
                "source": document.get("source_url") or "",
                "metadata": {
                    "document_id": hit.document_id,
                    "score": hit.score,
                },
            }
        )
    return context_items


def _fallback_answer(org_id: str | None, hits: list[SearchHitEntity]) -> tuple[str, list[CitationEntity]]:
    citations = _to_citations(hits)
    if citations:
        answer = (
            "Toi tim thay cac tai lieu lien quan nhat trong Elasticsearch cho cau hoi cua ban: "
            + " ".join([f"- {item.file_name} ({item.source_url})" for item in citations])
            + " Ban co the mo cac nguon nay de doi chieu noi dung goc."
        )
        return answer, citations
    if org_id:
        return "Chua tim thay tai lieu phu hop trong Elasticsearch cho cau hoi nay.", []
    return (
        "Workspace ca nhan hien chua gan kho tai lieu noi bo. "
        "Ban co the tao to chuc hoac chon workspace to chuc de hoi dap theo tai lieu."
    ), []


def _run_search_query_refinement(question: str, session_id: str, user_id: str) -> str:
    try:
        inference = create_inference(
            {
                "conversation_id": session_id,
                "user_id": user_id,
                "use_case": "chat_advisory",
                "question": question,
                "history": [],
                "external_contexts": [],
                "system_prompt": (
                    "Ban la bo xu ly truy van tim kiem noi bo. "
                    "Hay viet lai cau hoi cua nguoi dung thanh mot truy van tim kiem ngan gon bang tieng Viet. "
                    "Chi tra ve duy nhat mot dong query, khong giai thich them."
                ),
                "metadata": {"phase": "rewrite_query"},
            }
        )
        refined = (((inference or {}).get("response") or {}).get("response_text") or "").strip()
        refined = refined.splitlines()[0].strip().strip('"').strip("'") if refined else ""
        return refined or question
    except HTTPException:
        return question


def _search_context(org_id: str, question: str, session_id: str, user_id: str, db: Session) -> tuple[str, list[SearchHitEntity]]:
    search_query = _run_search_query_refinement(question, session_id, user_id)
    try:
        hits = query_documents(f"org-{org_id}-documents", search_query, size=5)
        if hits:
            return search_query, hits
        for document in documents_repository.list_documents_for_reindex(org_id, 50, db):
            metadata = parse_json_dict(document.metadata_json)
            bucket = metadata.get("bucket")
            object_key = metadata.get("object_key")
            if not bucket or not object_key:
                continue
            minio_response = get_file_from_minio(bucket, object_key)
            file_bytes = minio_response["Body"].read()
            extracted_text = extract_document_text(document.file_name, file_bytes)
            if not extracted_text:
                continue
            metadata["content_text"] = extracted_text
            document.metadata_json = json.dumps(metadata)
            index_document(document, content_text=extracted_text)
        db.commit()
        return search_query, query_documents(f"org-{org_id}-documents", search_query, size=5)
    except HTTPException:
        return search_query, []


def _run_answer_inference(
    *,
    org_id: str | None,
    payload: models.ChatAsk,
    session: db_entities.ChatSession,
    hits: list[SearchHitEntity],
    db: Session,
) -> tuple[str, list[CitationEntity]]:
    citations = _to_citations(hits)
    contexts = _to_context_items(hits)
    if org_id and not contexts:
        return _fallback_answer(org_id, hits)

    try:
        inference = create_inference(
            {
                "conversation_id": session.id,
                "organization_id": org_id,
                "user_id": payload.user_id,
                "use_case": "chat_advisory",
                "question": payload.question,
                "history": _to_history_payload(session.id, db),
                "external_contexts": contexts,
                "system_prompt": (
                    "Ban la tro ly doanh nghiep noi bo. "
                    "Truoc tien hay doc cau hoi cua nguoi dung. "
                    "Neu co context duoc cung cap, chi dua tren context do de tra loi ngan gon, ro rang, co cau truc. "
                    "Neu context chua du, hay noi ro phan nao chua du thong tin."
                ),
                "metadata": {
                    "phase": "final_answer",
                    "organization_id": org_id,
                    "search_hit_count": len(hits),
                },
            }
        )
        answer = (((inference or {}).get("response") or {}).get("response_text") or "").strip()
        if answer:
            return answer, citations
    except HTTPException:
        pass

    return _fallback_answer(org_id, hits)


def _serialize_search_hits(hits: list[SearchHitEntity]) -> list[dict]:
    return [
        jsonable_encoder(
            models.DocumentSearchHit(
                document_id=hit.document_id,
                file_name=hit.document.get("file_name") or hit.document_id,
                source_url=hit.document.get("source_url") or "",
                score=hit.score,
                document=hit.document,
            )
        )
        for hit in hits
    ]


def _serialize_citations(citations: list[CitationEntity]) -> list[dict]:
    return [jsonable_encoder(chat_dto.to_citation_model(item)) for item in citations]


def _stream_event(event_type: str, **payload) -> str:
    return json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n"


def _stream_answer_chunks(answer: str):
    for index in range(0, len(answer), 48):
        yield answer[index:index + 48]


@router.get("/organizations/{org_id}/chat/suggestions", response_model=list[str], tags=["Chat"], summary="Lay goi y cau hoi theo to chuc")
def chat_suggestions(org_id: str, acting_user_id: str, db: Session = Depends(get_db)) -> list[str]:
    _require_permission(org_id, acting_user_id, "chat_advisory", db)
    return _organization_suggestions()


@router.get("/chat/personal/suggestions", response_model=list[str], tags=["Chat"], summary="Lay goi y cau hoi theo workspace ca nhan")
def personal_chat_suggestions(acting_user_id: str, db: Session = Depends(get_db)) -> list[str]:
    return _personal_suggestions()


@router.get("/organizations/{org_id}/chat/sessions", response_model=list[models.ChatSessionRead], tags=["Chat"], summary="Lay chat history theo context to chuc")
def list_chat_sessions(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen chat_advisory."),
    db: Session = Depends(get_db),
) -> list[models.ChatSessionRead]:
    _require_permission(org_id, acting_user_id, "chat_advisory", db)
    return chat_dto.to_chat_session_models(chat_repository.list_chat_sessions(org_id, acting_user_id, db))


@router.get("/chat/personal/sessions", response_model=list[models.ChatSessionRead], tags=["Chat"], summary="Lay chat history theo workspace ca nhan")
def list_personal_chat_sessions(
    acting_user_id: str = Query(..., description="User dang xem workspace ca nhan."),
    db: Session = Depends(get_db),
) -> list[models.ChatSessionRead]:
    return chat_dto.to_chat_session_models(chat_repository.list_personal_chat_sessions(acting_user_id, db))


@router.post("/organizations/{org_id}/chat/sessions", response_model=models.ChatSessionRead, status_code=status.HTTP_201_CREATED, tags=["Chat"], summary="Tao chat session rong")
def create_chat_session(org_id: str, payload: models.ChatSessionCreate, db: Session = Depends(get_db)) -> models.ChatSessionRead:
    _require_permission(org_id, payload.user_id, "chat_advisory", db)
    session = chat_repository.create_chat_session(org_id, payload.user_id, payload.context_type, payload.title, db)
    return chat_dto.to_chat_session_model(session)


@router.get("/chat/sessions/{session_id}/messages", response_model=list[models.ChatMessageRead], tags=["Chat"], summary="Lay message trong mot chat session")
def list_chat_messages(
    session_id: str,
    acting_user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> list[models.ChatMessageRead]:
    session = _get_session_or_404(session_id, db)
    if session.organization_id:
        _require_permission(session.organization_id, acting_user_id, "chat_advisory", db)
    elif session.user_id != acting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc xem chat cua user khac.")
    return chat_dto.to_chat_message_models(chat_repository.list_chat_messages(session_id, db))


@router.post("/organizations/{org_id}/chat/ask", response_model=models.ChatAnswer, tags=["Chat"], summary="Hoi dap theo tai lieu noi bo to chuc")
def ask_chat(org_id: str, payload: models.ChatAsk, db: Session = Depends(get_db)) -> models.ChatAnswer:
    _require_permission(org_id, payload.user_id, "chat_advisory", db)
    session = _get_or_create_session(org_id, payload, db)
    _search_query, hits = _search_context(org_id, payload.question, session.id, payload.user_id, db)
    answer, citations = _run_answer_inference(org_id=org_id, payload=payload, session=session, hits=hits, db=db)
    result = chat_repository.save_chat_answer(session, payload.question, answer, citations, hits, db)
    return chat_dto.to_chat_answer_model(result)


@router.post("/chat/personal/ask", response_model=models.ChatAnswer, tags=["Chat"], summary="Hoi dap theo workspace ca nhan")
def ask_personal_chat(payload: models.ChatAsk, db: Session = Depends(get_db)) -> models.ChatAnswer:
    session = _get_or_create_session(None, payload, db)
    answer, citations = _run_answer_inference(org_id=None, payload=payload, session=session, hits=[], db=db)
    result = chat_repository.save_chat_answer(session, payload.question, answer, citations, [], db)
    return chat_dto.to_chat_answer_model(result)


@router.post("/organizations/{org_id}/chat/ask/stream", tags=["Chat"], summary="Hoi dap theo tai lieu noi bo to chuc voi stream")
def stream_chat(org_id: str, payload: models.ChatAsk, db: Session = Depends(get_db)) -> StreamingResponse:
    def event_stream():
        try:
            _require_permission(org_id, payload.user_id, "chat_advisory", db)
            session = _get_or_create_session(org_id, payload, db)
            yield _stream_event("session", session=jsonable_encoder(chat_dto.to_chat_session_model(session)))
            yield _stream_event("status", stage="understanding", message="Dang hieu cau hoi va toi uu truy van tim kiem.")
            search_query, hits = _search_context(org_id, payload.question, session.id, payload.user_id, db)
            citations = _to_citations(hits)
            yield _stream_event("status", stage="searching", message="Dang tim tai lieu lien quan trong Elasticsearch.")
            yield _stream_event(
                "search_results",
                query=search_query,
                hits=_serialize_search_hits(hits),
                citations=_serialize_citations(citations),
            )
            yield _stream_event("status", stage="reasoning", message="Dang tong hop context va soan cau tra loi.")
            answer, citations = _run_answer_inference(org_id=org_id, payload=payload, session=session, hits=hits, db=db)
            yield _stream_event("status", stage="answering", message="Dang tra loi.")
            for chunk in _stream_answer_chunks(answer):
                yield _stream_event("answer_chunk", chunk=chunk)
                time.sleep(0.01)
            result = chat_repository.save_chat_answer(session, payload.question, answer, citations, hits, db)
            yield _stream_event("complete", response=jsonable_encoder(chat_dto.to_chat_answer_model(result)))
        except HTTPException:
            yield _stream_event("error", message="Khong the xu ly cau hoi luc nay.")
        except Exception:
            yield _stream_event("error", message="Khong the xu ly cau hoi luc nay.")

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/chat/personal/ask/stream", tags=["Chat"], summary="Hoi dap workspace ca nhan voi stream")
def stream_personal_chat(payload: models.ChatAsk, db: Session = Depends(get_db)) -> StreamingResponse:
    def event_stream():
        try:
            session = _get_or_create_session(None, payload, db)
            yield _stream_event("session", session=jsonable_encoder(chat_dto.to_chat_session_model(session)))
            yield _stream_event("status", stage="understanding", message="Dang hieu cau hoi.")
            answer, citations = _run_answer_inference(org_id=None, payload=payload, session=session, hits=[], db=db)
            yield _stream_event("status", stage="answering", message="Dang tra loi.")
            for chunk in _stream_answer_chunks(answer):
                yield _stream_event("answer_chunk", chunk=chunk)
                time.sleep(0.01)
            result = chat_repository.save_chat_answer(session, payload.question, answer, citations, [], db)
            yield _stream_event("complete", response=jsonable_encoder(chat_dto.to_chat_answer_model(result)))
        except HTTPException:
            yield _stream_event("error", message="Khong the xu ly cau hoi luc nay.")
        except Exception:
            yield _stream_event("error", message="Khong the xu ly cau hoi luc nay.")

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/chat/messages/{message_id}/feedback", response_model=models.FeedbackRead, status_code=status.HTTP_201_CREATED, tags=["Chat"], summary="Gui feedback cho cau tra loi")
def create_feedback(message_id: str, payload: models.FeedbackCreate, db: Session = Depends(get_db)) -> models.FeedbackRead:
    message = db.get(db_entities.ChatMessage, message_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message khong ton tai.")
    session = _get_session_or_404(message.session_id, db)
    if session.organization_id:
        _require_permission(session.organization_id, payload.user_id, "chat_advisory", db)
    elif session.user_id != payload.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc gui feedback cho chat cua user khac.")
    feedback = chat_repository.create_feedback(message_id, payload.user_id, payload.rating, payload.comment, db)
    return chat_dto.to_feedback_model(feedback)


@router.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chat"], summary="Xoa mot doan chat")
def delete_chat_session(
    session_id: str,
    acting_user_id: str = Query(..., description="User thuc hien thao tac xoa."),
    db: Session = Depends(get_db),
) -> None:
    session = _get_session_or_404(session_id, db)
    if session.organization_id:
        _require_permission(session.organization_id, acting_user_id, "delete_chat_sessions", db)
    elif session.user_id != acting_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Khong duoc xoa chat cua user khac.")
    chat_repository.delete_chat_session(session, db)
