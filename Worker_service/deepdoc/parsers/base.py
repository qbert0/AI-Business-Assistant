from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ParsedDocument:
    text: str
    markdown: str
    source_name: str
    parser_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseParser(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse_bytes(self, file_bytes: bytes, source_name: str) -> ParsedDocument:
        raise NotImplementedError

    def parse_file(self, file_path: str | Path) -> ParsedDocument:
        path = Path(file_path)
        return self.parse_bytes(path.read_bytes(), path.name)
