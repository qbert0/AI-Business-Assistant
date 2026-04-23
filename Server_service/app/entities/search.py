from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SearchDocumentEntity:
    index_name: str
    document_id: str
    document: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SearchHitEntity:
    index_name: str
    document_id: str
    score: float | None = None
    document: dict[str, Any] = field(default_factory=dict)
