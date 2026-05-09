from dataclasses import dataclass, field
from typing import Literal

from app.entities import database as db_entities
from app.entities.search import SearchHitEntity


PreviewKind = Literal["text", "image", "pdf", "download"]


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
