from dataclasses import dataclass, field

from app.entities import database as db_entities
from app.entities.search import SearchHitEntity


@dataclass(slots=True)
class DocumentPipelineEntity:
    document: db_entities.Document
    events: list[db_entities.PipelineEvent] = field(default_factory=list)


@dataclass(slots=True)
class DocumentSearchResultEntity:
    hits: list[SearchHitEntity] = field(default_factory=list)
