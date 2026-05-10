import json

from sqlalchemy.orm import Session

from app.entities import database as db_entities
from app.repositories.common import parse_json_dict


def get_organization(org_id: str, db: Session) -> db_entities.Organization | None:
    return db.get(db_entities.Organization, org_id)


def get_user(user_id: str, db: Session) -> db_entities.User | None:
    return db.get(db_entities.User, user_id)


def create_document(
    *,
    org_id: str,
    uploaded_by_user_id: str,
    file_name: str,
    source_url: str,
    metadata_json: str,
    vector_index: str,
    db: Session,
) -> db_entities.Document:
    document = db_entities.Document(
        organization_id=org_id,
        uploaded_by_user_id=uploaded_by_user_id,
        file_name=file_name,
        source_url=source_url,
        vector_index=vector_index,
        metadata_json=metadata_json,
    )
    db.add(document)
    db.flush()
    return document


def create_pipeline_event(
    *,
    organization_id: str,
    document_id: str,
    actor_user_id: str | None,
    stage: str,
    status: str,
    message: str | None,
    db: Session,
) -> db_entities.PipelineEvent:
    event = db_entities.PipelineEvent(
        organization_id=organization_id,
        document_id=document_id,
        actor_user_id=actor_user_id,
        stage=stage,
        status=status,
        message=message,
    )
    db.add(event)
    db.flush()
    return event


def save_document(db: Session) -> None:
    db.commit()


def refresh_document(document: db_entities.Document, db: Session) -> db_entities.Document:
    db.refresh(document)
    return document


def delete_document(document: db_entities.Document, db: Session) -> None:
    db.delete(document)
    db.commit()


def list_documents(
    org_id: str,
    status_filter: str | None,
    skip: int,
    limit: int,
    db: Session,
) -> list[db_entities.Document]:
    query = db.query(db_entities.Document).filter(db_entities.Document.organization_id == org_id)
    if status_filter:
        query = query.filter(db_entities.Document.status == status_filter)
    return query.order_by(db_entities.Document.created_at.desc()).offset(skip).limit(limit).all()


def get_document(document_id: str, db: Session) -> db_entities.Document | None:
    return db.get(db_entities.Document, document_id)


def list_pipeline_events(document_id: str, db: Session) -> list[db_entities.PipelineEvent]:
    return (
        db.query(db_entities.PipelineEvent)
        .filter(db_entities.PipelineEvent.document_id == document_id)
        .order_by(db_entities.PipelineEvent.created_at.asc())
        .all()
    )


def update_document_status_fields(
    document: db_entities.Document,
    *,
    status_value: str | None,
    chunk_count: int | None,
    embedding_model: str | None,
    vector_index: str | None,
) -> db_entities.Document:
    if status_value is not None:
        document.status = status_value
    if chunk_count is not None:
        document.chunk_count = str(chunk_count)
    if embedding_model is not None:
        document.embedding_model = embedding_model
    if vector_index is not None:
        document.vector_index = vector_index
    return document


def merge_document_metadata(document: db_entities.Document, metadata_patch: dict) -> db_entities.Document:
    def deep_merge(base: dict, patch: dict) -> dict:
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    metadata = parse_json_dict(document.metadata_json)
    document.metadata_json = json.dumps(deep_merge(metadata, metadata_patch))
    return document


def list_documents_for_reindex(org_id: str, limit: int, db: Session) -> list[db_entities.Document]:
    return (
        db.query(db_entities.Document)
        .filter(db_entities.Document.organization_id == org_id)
        .order_by(db_entities.Document.updated_at.desc())
        .limit(limit)
        .all()
    )
