import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.entities.chat import CitationEntity
from app.entities.search import SearchHitEntity


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [clean_text(item) for item in value if clean_text(item)]


def coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    if value is None:
        return default
    return bool(value)


def parse_json_object(raw_text: str) -> dict[str, Any]:
    text = clean_text(raw_text)
    if not text:
        return {}

    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


@dataclass(slots=True)
class AgentWorkflowEvent:
    event_type: str
    stage: str
    agent: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AgentWorkflowState:
    organization_id: str | None
    session_id: str
    user_id: str
    question: str
    history: list[dict[str, Any]] = field(default_factory=list)
    plan_summary: str = ""
    retrieval_queries: list[str] = field(default_factory=list)
    needs_document_search: bool = False
    search_attempts: list[dict[str, Any]] = field(default_factory=list)
    search_hits: list[SearchHitEntity] = field(default_factory=list)
    citations: list[CitationEntity] = field(default_factory=list)
    contexts: list[dict[str, Any]] = field(default_factory=list)
    draft_answer: str = ""
    verified_answer: str = ""
    answer: str = ""
    verification_notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    name = "base"
    stage = "base"
    start_message = "Đang xử lý."

    @abstractmethod
    def run(self, state: AgentWorkflowState) -> AgentWorkflowState:
        raise NotImplementedError

    def start_event(self) -> AgentWorkflowEvent:
        return AgentWorkflowEvent(
            event_type="status",
            stage=self.stage,
            agent=self.name,
            message=self.start_message,
        )

    def finish_event(self, state: AgentWorkflowState) -> AgentWorkflowEvent:
        return AgentWorkflowEvent(
            event_type="status",
            stage=self.stage,
            agent=self.name,
            message=self.finish_message(state),
            payload=self.build_payload(state),
        )

    def finish_message(self, state: AgentWorkflowState) -> str:
        return "Đã xử lý xong bước này."

    def build_payload(self, state: AgentWorkflowState) -> dict[str, Any]:
        return {}

    def extra_events(self, state: AgentWorkflowState) -> list[AgentWorkflowEvent]:
        return []
