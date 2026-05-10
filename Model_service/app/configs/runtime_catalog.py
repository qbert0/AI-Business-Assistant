from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


CONFIG_FILE_PATH = Path(__file__).with_name("config.yaml")


def _map_provider_type(api_type: str | None) -> str:
    value = (api_type or "openai").strip().lower()
    if value in {"openai", "openai_compatible"}:
        return "openai_compatible"
    if value == "ollama":
        return "ollama"
    raise ValueError(f"Unsupported provider type in config: {api_type}")


@dataclass(slots=True)
class RuntimeModelEntry:
    key: str
    provider_type: str
    model_name: str
    base_url: str
    api_key: str | None
    capabilities: list[str]
    parameters: dict[str, Any] = field(default_factory=dict)
    is_default: bool = False


@dataclass(slots=True)
class RuntimeModelCatalog:
    default_llm_model: str | None
    default_embedding_model: str | None
    llm_models: list[RuntimeModelEntry] = field(default_factory=list)
    embedding_models: list[RuntimeModelEntry] = field(default_factory=list)

    def all_models(self) -> list[RuntimeModelEntry]:
        return [*self.llm_models, *self.embedding_models]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _contains_model_reference(section: dict[str, Any], target_name: str | None) -> bool:
    if not target_name:
        return False
    if target_name in section:
        return True
    for value in section.values():
        if isinstance(value, dict) and str(value.get("model") or "") == target_name:
            return True
    return False


def _build_llm_entry(key: str, raw: dict[str, Any], default_name: str | None) -> RuntimeModelEntry:
    model_name = str(raw.get("model") or key)
    return RuntimeModelEntry(
        key=key,
        provider_type=_map_provider_type(raw.get("api_type")),
        model_name=model_name,
        base_url=str(raw.get("base_url") or "").rstrip("/"),
        api_key=raw.get("api_key"),
        capabilities=["chat"],
        parameters={
            "temperature": raw.get("temperature"),
            "max_tokens": raw.get("max_token"),
            "timeout": raw.get("timeout"),
            "stream": raw.get("stream", True),
            "reasoning_effort": raw.get("reasoning_effort"),
            "config_key": key,
            "config_managed": True,
        },
        is_default=default_name in {key, model_name},
    )


def _build_embedding_entry(key: str, raw: dict[str, Any], default_name: str | None) -> RuntimeModelEntry:
    model_name = str(raw.get("model") or key)
    return RuntimeModelEntry(
        key=key,
        provider_type=_map_provider_type(raw.get("api_type")),
        model_name=model_name,
        base_url=str(raw.get("base_url") or "").rstrip("/"),
        api_key=raw.get("api_key"),
        capabilities=["embedding"],
        parameters={
            "dimensions": raw.get("dimensions"),
            "timeout": raw.get("timeout"),
            "config_key": key,
            "config_managed": True,
        },
        is_default=default_name in {key, model_name},
    )


def load_runtime_model_catalog(path: Path = CONFIG_FILE_PATH) -> RuntimeModelCatalog:
    raw = _read_yaml(path)
    llm_default_config = raw.get("llm") or {}
    embedding_default_config = raw.get("embedding") or {}
    llm_default_name = llm_default_config.get("model")
    embedding_default_name = embedding_default_config.get("model")
    llm_section = dict(raw.get("models") or {})
    embedding_section = dict(raw.get("embeddings") or {})

    if llm_default_name and not _contains_model_reference(llm_section, llm_default_name):
        llm_section[llm_default_name] = llm_default_config
    if embedding_default_name and not _contains_model_reference(embedding_section, embedding_default_name):
        embedding_section[embedding_default_name] = embedding_default_config

    llm_models = [
        _build_llm_entry(key, value or {}, llm_default_name)
        for key, value in llm_section.items()
    ]
    embedding_models = [
        _build_embedding_entry(key, value or {}, embedding_default_name)
        for key, value in embedding_section.items()
    ]

    return RuntimeModelCatalog(
        default_llm_model=llm_default_name,
        default_embedding_model=embedding_default_name,
        llm_models=llm_models,
        embedding_models=embedding_models,
    )
