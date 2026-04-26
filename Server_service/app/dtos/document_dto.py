from app import models
from app.entities import database as db_entities
from app.entities.document import DocumentPipelineEntity, DocumentPreviewEntity, DocumentSearchResultEntity
from app.entities.search import SearchHitEntity
from app.repositories.common import parse_json_dict


def to_document_model(document: db_entities.Document) -> models.DocumentRead:
    return models.DocumentRead(
        id=document.id,
        organization_id=document.organization_id,
        uploaded_by_user_id=document.uploaded_by_user_id,
        file_name=document.file_name,
        source_url=document.source_url,
        status=document.status,
        chunk_count=int(document.chunk_count or 0),
        embedding_model=document.embedding_model,
        vector_index=document.vector_index,
        metadata=parse_json_dict(document.metadata_json),
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def to_document_models(documents: list[db_entities.Document]) -> list[models.DocumentRead]:
    return [to_document_model(document) for document in documents]


def to_pipeline_event_model(event: db_entities.PipelineEvent) -> models.PipelineEventRead:
    return models.PipelineEventRead(
        id=event.id,
        organization_id=event.organization_id,
        document_id=event.document_id,
        actor_user_id=event.actor_user_id,
        stage=event.stage,
        status=event.status,
        message=event.message,
        created_at=event.created_at,
    )


def to_document_pipeline_model(entity: DocumentPipelineEntity) -> models.DocumentPipeline:
    return models.DocumentPipeline(
        document=to_document_model(entity.document),
        events=[to_pipeline_event_model(event) for event in entity.events],
    )


def to_document_preview_model(entity: DocumentPreviewEntity) -> models.DocumentPreviewRead:
    return models.DocumentPreviewRead(
        document_id=entity.document.id,
        file_name=entity.document.file_name,
        kind=entity.kind,
        content=entity.content,
        message=entity.message,
    )


def to_document_search_hit_model(hit: SearchHitEntity) -> models.DocumentSearchHit:
    document_id = hit.document.get("document_id") or hit.document_id
    return models.DocumentSearchHit(
        document_id=document_id,
        file_name=hit.document.get("file_name") or document_id,
        source_url=hit.document.get("source_url") or "",
        score=hit.score,
        document=hit.document,
    )


def to_document_search_hit_models(entity: DocumentSearchResultEntity) -> list[models.DocumentSearchHit]:
    return [to_document_search_hit_model(hit) for hit in entity.hits]
