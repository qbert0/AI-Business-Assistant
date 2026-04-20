from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class SearchDocument:
    index_name: str
    document_id: str
    document: dict[str, Any] = field(default_factory=dict)
    result: str | None = None
    version: int | None = None


@dataclass(slots=True)
class SearchDeleteResult:
    index_name: str
    document_id: str
    deleted: bool
    result: str | None = None


class AbstractSearchEngine(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def ping(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_document(
        self,
        index_name: str,
        document_id: str,
        document: Mapping[str, Any],
        *,
        refresh: bool = True,
    ) -> SearchDocument:
        raise NotImplementedError

    @abstractmethod
    def get_document(self, index_name: str, document_id: str) -> SearchDocument:
        raise NotImplementedError

    @abstractmethod
    def update_document(
        self,
        index_name: str,
        document_id: str,
        document: Mapping[str, Any],
        *,
        refresh: bool = True,
    ) -> SearchDocument:
        raise NotImplementedError

    @abstractmethod
    def delete_document(
        self,
        index_name: str,
        document_id: str,
        *,
        refresh: bool = True,
    ) -> SearchDeleteResult:
        raise NotImplementedError
