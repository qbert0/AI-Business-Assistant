from dataclasses import dataclass, field

from app.entities import database as db_entities
from app.entities.search import SearchHitEntity
from app.services.document_preview import PreviewKind


@dataclass(slots=True)
class DocumentPipelineEntity:
    document: db_entities.Document
    events: list[db_entities.PipelineEvent] = field(default_factory=list)


@dataclass(slots=True)
class DocumentSearchResultEntity:
    hits: list[SearchHitEntity] = field(default_factory=list)


@dataclass(slots=True)
class DocumentPreviewEntity:
    document: db_entities.Document
    kind: PreviewKind
    content: str | None = None
    message: str | None = None
