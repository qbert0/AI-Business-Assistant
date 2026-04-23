from dataclasses import dataclass, field

from app.entities import database as db_entities
from app.entities.search import SearchHitEntity


@dataclass(slots=True)
class CitationEntity:
    document_id: str
    file_name: str
    source_url: str


@dataclass(slots=True)
class ChatAnswerEntity:
    session: db_entities.ChatSession
    user_message: db_entities.ChatMessage
    assistant_message: db_entities.ChatMessage
    answer: str
    citations: list[CitationEntity] = field(default_factory=list)
    search_hits: list[SearchHitEntity] = field(default_factory=list)
