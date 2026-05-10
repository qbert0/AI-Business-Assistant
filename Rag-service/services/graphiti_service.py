from __future__ import annotations

import asyncio
import json
import re
import threading
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from conn.model_service_client import ModelServiceClient
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt
from utils.common import OutputParser
from utils.constants import (
    LLM_RESPONSE_LOG,
    LLM_RESPONSE_LOG_MAX_CHARS,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USERNAME,
)
from utils.logs import llm_response_logger, logger
from utils.prompt_loader import load_prompt

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.embedder.client import EmbedderClient
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_NODE_DISTANCE,
    EDGE_HYBRID_SEARCH_RRF,
    NODE_HYBRID_SEARCH_RRF,
)
from graphiti_core.utils.bulk_utils import RawEpisode

class StructuredOutputFormatError(ValueError):
    pass


class GraphitiModelServiceLLMClient(LLMClient):  # type: ignore[misc]
    RESPONSE_SCHEMA_PLACEHOLDER = "__RESPONSE_SCHEMA__"
    STRUCTURED_OUTPUT_PROMPT = load_prompt("graphiti_structured_output.txt")
    STRUCTURED_OUTPUT_FEWSHOT_PROMPT = load_prompt("graphiti_structured_output_fewshot.txt")
    RETRY_REPAIR_PROMPT = (
        "Your previous response was invalid. Return only one final ```json fenced block that contains "
        "one valid JSON object matching the expected schema. Do not include explanations, reasoning, "
        "candidate lists, or schema definitions."
    )

    def __init__(
        self,
        model_service_client: ModelServiceClient,
        config: Optional[LLMConfig] = None,
    ) -> None:
        super().__init__(config=config or LLMConfig(api_key="model-service", model="model-service"))  # type: ignore[call-arg]
        self.model_service_client = model_service_client

    async def _generate_response(
        self,
        messages,
        response_model=None,
        max_tokens=None,
        model_size=None,
        **kwargs,
    ) -> dict[str, Any] | Any:
        system_messages: list[str] = []
        history: list[dict[str, str]] = []
        user_parts: list[str] = []

        for message in messages:
            role = self._message_field(message, "role", "user")
            content = self._message_field(message, "content", "")
            if role == "system":
                system_messages.append(content)
            elif role == "user":
                user_parts.append(content)
                history.append({"role": role, "content": content})
            else:
                history.append({"role": role, "content": content})

        question = "\n\n".join(user_parts).strip() or "Return a valid JSON response."
        system_prompt = "\n\n".join(part for part in system_messages if part).strip() or None
        if response_model is not None:
            system_prompt = self._build_structured_system_prompt(
                base_system_prompt=system_prompt,
                response_model=response_model,
            )

        if response_model is None:
            inference_result = await self.model_service_client.create_inference(
                question=question,
                system_prompt=system_prompt,
                history=history[:-1] if history and history[-1]["role"] == "user" else history,
                max_tokens=self._normalize_max_tokens(max_tokens),
                temperature=0.0,
                metadata={
                    "graphiti_model_size": self._safe_metadata_value(model_size),
                    "response_model": getattr(response_model, "__name__", None),
                },
            )
            response_text = (
                inference_result.get("response", {}) or {}
            ).get("response_text", "")
            return {"content": response_text}

        parsed, response_text = await self._request_structured_response(
            question=question,
            system_prompt=system_prompt,
            history=history[:-1] if history and history[-1]["role"] == "user" else history,
            response_model=response_model,
            max_tokens=self._normalize_max_tokens(max_tokens),
            model_size=model_size,
        )

        return parsed

    async def _request_structured_response(
        self,
        *,
        question: str,
        system_prompt: str | None,
        history: list[dict[str, str]],
        response_model: Any,
        max_tokens: int | None,
        model_size: Any,
    ) -> tuple[dict[str, Any] | Any, str]:
        metadata = {
            "graphiti_model_size": self._safe_metadata_value(model_size),
            "response_model": getattr(response_model, "__name__", None),
        }

        response_text = ""
        parsed: dict[str, Any] | Any | None = None

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(StructuredOutputFormatError),
            reraise=True,
        ):
            with attempt:
                attempt_number = attempt.retry_state.attempt_number
                attempt_stage = "initial" if attempt_number == 1 else "retry_repair"
                attempt_prompt = system_prompt
                logger.info(
                    "Structured response attempt started "
                    f"response_model={getattr(response_model, '__name__', None)} "
                    f"attempt={attempt_number}"
                )
                if attempt_number > 1:
                    logger.warning(
                        "Model service returned invalid structured output; retrying with repair prompt. "
                        f"response_model={getattr(response_model, '__name__', None)} "
                        f"attempt={attempt_number}"
                    )
                    attempt_prompt = "\n\n".join(
                        part
                        for part in [system_prompt, self.RETRY_REPAIR_PROMPT]
                        if part
                    )

                inference_result = await self.model_service_client.create_inference(
                    question=question,
                    system_prompt=attempt_prompt,
                    history=history,
                    max_tokens=max_tokens,
                    temperature=0.0,
                    metadata={
                        **metadata,
                        "structured_attempt": attempt_number,
                    },
                )
                response_text = ((inference_result.get("response", {}) or {}).get("response_text", ""))
                self._log_structured_exchange(
                    stage=attempt_stage,
                    response_model=response_model,
                    question=question,
                    system_prompt=attempt_prompt,
                    history=history,
                    response_text=response_text,
                )
                parsed = self._parse_structured_json_response(response_text)
                if hasattr(response_model, "model_validate"):
                    try:
                        validated = response_model.model_validate(parsed)
                        if hasattr(validated, "model_dump"):
                            parsed = validated.model_dump(by_alias=True)
                    except Exception as exc:
                        logger.error(
                            "Structured validation failed in Graphiti LLM adapter: "
                            f"{exc}. response_preview={response_text[:1200]}"
                        )
                        if LLM_RESPONSE_LOG:
                            llm_response_logger.error(
                                json.dumps(
                                    {
                                        "stage": "validation_error",
                                        "response_model": getattr(response_model, "__name__", None),
                                        "response_preview": self._truncate_for_log(response_text),
                                        "error": str(exc),
                                    },
                                    ensure_ascii=False,
                                )
                            )
                        raise StructuredOutputFormatError(
                            f"Model service returned JSON that failed schema validation: {exc}"
                        ) from exc
                logger.info(
                    "Structured response attempt succeeded "
                    f"response_model={getattr(response_model, '__name__', None)} "
                    f"attempt={attempt_number}"
                )

        if parsed is None:
            raise StructuredOutputFormatError("Structured output retry completed without parsed data")

        self._log_parsed_structured_response(
            response_model=response_model,
            parsed=parsed,
        )
        return parsed, response_text

    @staticmethod
    def _parse_structured_json_response(response_text: str) -> dict[str, Any]:
        json_text = ""
        try:
            json_text = GraphitiModelServiceLLMClient._extract_structured_json_text(response_text)
            parsed = json.loads(json_text)
        except Exception as fenced_exc:
            cls_or_self = GraphitiModelServiceLLMClient
            if LLM_RESPONSE_LOG:
                llm_response_logger.error(
                    json.dumps(
                        {
                            "stage": "parse_error",
                            "response_preview": cls_or_self._truncate_for_log(response_text),
                            "fenced_json_error": str(fenced_exc),
                        },
                        ensure_ascii=False,
                    )
                )
            logger.error(
                "Model service did not return a valid ```json fenced block for Graphiti structured output. "
                f"response_preview={response_text[:1200]}"
            )
            raise StructuredOutputFormatError(
                "Model service did not return a valid ```json fenced block for structured output"
            ) from fenced_exc

        if not isinstance(parsed, dict):
            if LLM_RESPONSE_LOG:
                llm_response_logger.error(
                    json.dumps(
                        {
                            "stage": "non_object_response",
                            "response_preview": GraphitiModelServiceLLMClient._truncate_for_log(response_text),
                        },
                        ensure_ascii=False,
                    )
                )
            logger.error(
                "Model service returned structured output that is not a JSON object. "
                f"response_preview={response_text[:1200]}"
            )
            raise StructuredOutputFormatError("Model service returned structured output that is not a JSON object")

        if not parsed:
            if LLM_RESPONSE_LOG:
                llm_response_logger.error(
                    json.dumps(
                        {
                            "stage": "empty_object_response",
                            "response_preview": GraphitiModelServiceLLMClient._truncate_for_log(response_text),
                        },
                        ensure_ascii=False,
                    )
                )
            logger.error(
                "Model service returned an empty JSON object for Graphiti structured output. "
                f"response_preview={response_text[:1200]}"
            )
            raise StructuredOutputFormatError("Model service returned an empty JSON object for structured output")

        return parsed

    @staticmethod
    def _extract_structured_json_text(response_text: str) -> str:
        try:
            return OutputParser.parse_code(response_text, "json").strip()
        except Exception:
            pass

        fenced_match = re.search(r"```json\s*(.*?)(?:```|$)", response_text, re.DOTALL | re.IGNORECASE)
        if fenced_match:
            candidate = fenced_match.group(1).strip()
            if candidate:
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    balanced_candidate = GraphitiModelServiceLLMClient._extract_balanced_json_object(candidate)
                    if balanced_candidate:
                        return balanced_candidate

        balanced_response = GraphitiModelServiceLLMClient._extract_balanced_json_object(response_text)
        if balanced_response:
            return balanced_response

        raise StructuredOutputFormatError("No JSON object found in model response")

    @staticmethod
    def _extract_balanced_json_object(text: str) -> str | None:
        start = text.find("{")
        if start < 0:
            return None

        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == "\"":
                    in_string = False
                continue

            if char == "\"":
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : index + 1].strip()
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        return None

        return None

    @classmethod
    def _build_structured_system_prompt(
        cls,
        *,
        base_system_prompt: str | None,
        response_model: Any,
    ) -> str:
        schema_text = ""
        if hasattr(response_model, "model_json_schema"):
            schema_text = json.dumps(
                cls._safe_metadata_value(response_model.model_json_schema()),
                ensure_ascii=False,
            )

        prompt_parts = [
            part
            for part in [
                base_system_prompt,
                cls.STRUCTURED_OUTPUT_FEWSHOT_PROMPT,
                cls.STRUCTURED_OUTPUT_PROMPT.replace(
                    cls.RESPONSE_SCHEMA_PLACEHOLDER,
                    schema_text,
                ),
            ]
            if part
        ]
        return "\n\n".join(prompt_parts)

    @classmethod
    def _log_structured_exchange(
        cls,
        *,
        stage: str,
        response_model: Any,
        question: str,
        system_prompt: str | None,
        history: list[dict[str, str]],
        response_text: str,
    ) -> None:
        if not LLM_RESPONSE_LOG:
            return
        payload = {
            "stage": stage,
            "response_model": getattr(response_model, "__name__", None),
            "history_count": len(history),
            "question_preview": cls._truncate_for_log(question),
            "system_prompt_preview": cls._truncate_for_log(system_prompt or ""),
            "response_preview": cls._truncate_for_log(response_text),
        }
        llm_response_logger.info(json.dumps(payload, ensure_ascii=False))

    @classmethod
    def _log_parsed_structured_response(
        cls,
        *,
        response_model: Any,
        parsed: dict[str, Any],
    ) -> None:
        if not LLM_RESPONSE_LOG:
            return
        payload = {
            "stage": "parsed",
            "response_model": getattr(response_model, "__name__", None),
            "parsed_keys": sorted(parsed.keys()),
            "parsed_preview": cls._truncate_for_log(
                json.dumps(parsed, ensure_ascii=False)
            ),
        }
        llm_response_logger.info(json.dumps(payload, ensure_ascii=False))

    @staticmethod
    def _truncate_for_log(text: str) -> str:
        if len(text) <= LLM_RESPONSE_LOG_MAX_CHARS:
            return text
        return text[:LLM_RESPONSE_LOG_MAX_CHARS] + "\n...[truncated]"

    @staticmethod
    def _message_field(message: Any, field_name: str, default: str) -> str:
        if isinstance(message, dict):
            value = message.get(field_name, default)
        else:
            value = getattr(message, field_name, default)
        return str(value if value is not None else default)

    @staticmethod
    def _safe_metadata_value(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {
                str(key): GraphitiModelServiceLLMClient._safe_metadata_value(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple, set)):
            return [GraphitiModelServiceLLMClient._safe_metadata_value(item) for item in value]
        if hasattr(value, "value"):
            return GraphitiModelServiceLLMClient._safe_metadata_value(getattr(value, "value"))
        return str(value)

    @staticmethod
    def _normalize_max_tokens(value: Any) -> int | None:
        if value is None:
            return None
        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            return None
        return max(1, min(numeric_value, 8192))

class GraphitiModelServiceEmbedder(EmbedderClient):  # type: ignore[misc]
    def __init__(
        self,
        model_service_client: ModelServiceClient,
        embedding_dim: int | None = None,
        batch_size: int = 2,
        max_input_chars: int = 512,
    ) -> None:
        self.model_service_client = model_service_client
        self.embedding_dim = embedding_dim
        self.batch_size = max(1, batch_size)
        self.max_input_chars = max(256, max_input_chars)

    async def create(self, input_data) -> list[float]:
        text = self._prepare_text(input_data)
        result = await self._create_embeddings(
            [text],
            metadata={"source": "graphiti-embedder"},
        )
        return result["data"][0]["embedding"]

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        prepared_inputs = [self._prepare_text(item) for item in input_data_list]
        vectors: list[list[float]] = []

        for start in range(0, len(prepared_inputs), self.batch_size):
            chunk = prepared_inputs[start : start + self.batch_size]
            result = await self._create_embeddings(
                chunk,
                metadata={
                    "source": "graphiti-embedder-batch",
                    "batch_start": start,
                    "batch_size": len(chunk),
                },
            )
            vectors.extend(item["embedding"] for item in result.get("data", []))

        return vectors

    async def _create_embeddings(
        self,
        input_texts: list[str],
        *,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        effective_max_chars = self.max_input_chars
        trimmed_inputs = [
            text if len(text) <= effective_max_chars else text[:effective_max_chars]
            for text in input_texts
        ]

        logger.info(
            "Requesting embeddings from Model_service "
            f"count={len(trimmed_inputs)} "
            f"max_chars={effective_max_chars} "
            f"lengths={[len(text) for text in trimmed_inputs[:5]]}"
        )
        return await self.model_service_client.create_embeddings(
            trimmed_inputs,
            dimensions=self.embedding_dim,
            metadata={
                **metadata,
                "effective_max_chars": effective_max_chars,
            },
        )

    @staticmethod
    def _normalize_single_input(input_data) -> str:
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, list):
            return " ".join(str(item) for item in input_data)
        return str(input_data)

    def _prepare_text(self, input_data) -> str:
        normalized = self._normalize_single_input(input_data).strip()
        if len(normalized) <= self.max_input_chars:
            return normalized
        return normalized[: self.max_input_chars]


class GraphitiModelServiceCrossEncoder(CrossEncoderClient):  # type: ignore[misc]
    def __init__(self, model_service_client: ModelServiceClient, embedding_dim: int | None = None) -> None:
        self.embedder = GraphitiModelServiceEmbedder(
            model_service_client=model_service_client,
            embedding_dim=embedding_dim,
        )

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        if not passages:
            return []

        query_embedding = await self.embedder.create(query)
        passage_embeddings = await self.embedder.create_batch(passages)

        scored = [
            (passage, self._cosine_similarity(query_embedding, embedding))
            for passage, embedding in zip(passages, passage_embeddings)
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0

        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = sum(a * a for a in left) ** 0.5
        right_norm = sum(b * b for b in right) ** 0.5
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return numerator / (left_norm * right_norm)


class GraphitiService:
    SEARCH_CONTENT_PREVIEW_LIMIT = 4000
    SEARCH_SNIPPET_LIMIT = 1600

    def __init__(self) -> None:
        self.model_service_client = ModelServiceClient()
        self.graphiti: Optional[Graphiti] = None
        self._initialized = False
        self._schema_ready = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        if Graphiti is None:
            raise ImportError("graphiti-core is not installed in Rag-service")

        llm_client = GraphitiModelServiceLLMClient(
            model_service_client=self.model_service_client,
        )
        embedder = GraphitiModelServiceEmbedder(
            model_service_client=self.model_service_client,
        )
        cross_encoder = GraphitiModelServiceCrossEncoder(
            model_service_client=self.model_service_client,
        )

        self.graphiti = Graphiti(
            NEO4J_URI,
            NEO4J_USERNAME,
            NEO4J_PASSWORD,
            llm_client=llm_client,
            embedder=embedder,
            cross_encoder=cross_encoder,
        )
        self._initialized = True
        logger.info("GraphitiService initialized with Model_service-backed adapters")

    async def ensure_schema(self) -> None:
        if not self._initialized:
            await self.initialize()
        if self._schema_ready:
            return
        graphiti = self._require_graphiti()
        await graphiti.build_indices_and_constraints()
        self._schema_ready = True
        logger.info("Graphiti schema initialized")

    async def smoke_ingest_text(
        self,
        text: str,
        *,
        source_description: str = "compat smoke test",
        group_id: Optional[str] = None,
    ) -> dict[str, Any]:
        await self.ensure_schema()
        graphiti = self._require_graphiti()

        episode_name = f"compat-smoke-{uuid4()}"
        effective_group_id = group_id or f"compat-{uuid4()}"
        result = await graphiti.add_episode(
            name=episode_name,
            episode_body=text,
            source_description=source_description,
            reference_time=datetime.now(timezone.utc),
            source=EpisodeType.text,  # type: ignore[attr-defined]
            group_id=effective_group_id,
        )

        created = await graphiti.get_nodes_and_edges_by_episode([result.episode.uuid])
        return {
            "group_id": effective_group_id,
            "episode_uuid": result.episode.uuid,
            "episode_name": result.episode.name,
            "created_counts": {
                "episodic_edges": len(result.episodic_edges),
                "nodes": len(result.nodes),
                "edges": len(result.edges),
                "communities": len(result.communities),
                "community_edges": len(result.community_edges),
            },
            "queried_counts": {
                "nodes": len(created.nodes),
                "edges": len(created.edges),
                "episodes": len(created.episodes),
                "communities": len(created.communities),
            },
            "node_preview": [
                {
                    "uuid": node.uuid,
                    "name": node.name,
                    "summary": (node.summary or "")[:200],
                }
                for node in created.nodes[:5]
            ],
            "edge_preview": [
                {
                    "uuid": edge.uuid,
                    "fact": edge.fact,
                }
                for edge in created.edges[:5]
            ],
        }

    async def ingest_chunks(
        self,
        *,
        document_id: str,
        document_name: str,
        source: str,
        chunks: list[dict[str, Any]],
        source_description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self.ensure_schema()
        graphiti = self._require_graphiti()

        if not chunks:
            raise ValueError("chunks must not be empty")

        metadata = metadata or {}
        effective_group_id = self._build_group_id(document_id=document_id, metadata=metadata)
        effective_source_description = source_description or (
            f"Document {document_name} ingested from {source}"
        )

        raw_episodes: list[RawEpisode] = []
        prepared_chunks: list[dict[str, Any]] = []

        for index, chunk in enumerate(chunks, start=1):
            chunk_id = str(chunk.get("chunk_id") or f"{document_id}-chunk-{index}")
            content = str(chunk.get("content") or "").strip()
            if not content:
                raise ValueError(f"chunk {chunk_id} has empty content")

            chunk_metadata = chunk.get("metadata")
            if not isinstance(chunk_metadata, dict):
                chunk_metadata = {}

            episode_name = f"{document_name}::{chunk_id}"
            chunk_description = self._build_chunk_source_description(
                base_description=effective_source_description,
                document_id=document_id,
                chunk_id=chunk_id,
                source=source,
                metadata={**metadata, **chunk_metadata},
            )

            logger.info(
                "Graphiti ingest chunk started "
                f"document_id={document_id} "
                f"chunk_index={index}/{len(chunks)} "
                f"chunk_id={chunk_id} "
                f"content_length={len(content)}"
            )

            raw_episodes.append(
                RawEpisode(
                    name=episode_name,
                    content=content,
                    source=EpisodeType.text,
                    source_description=chunk_description,
                    reference_time=datetime.now(timezone.utc),
                )
            )
            prepared_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "episode_name": episode_name,
                    "content_length": len(content),
                }
            )

        logger.info(
            "Graphiti ingest bulk started "
            f"document_id={document_id} "
            f"group_id={effective_group_id} "
            f"chunk_count={len(raw_episodes)}"
        )

        bulk_result = await graphiti.add_episode_bulk(
            bulk_episodes=raw_episodes,
            group_id=effective_group_id,
        )

        episode_results = []
        for index, episode in enumerate(bulk_result.episodes):
            chunk_info = prepared_chunks[index] if index < len(prepared_chunks) else {}
            episode_results.append(
                {
                    "episode_uuid": episode.uuid,
                    "episode_name": episode.name,
                    "chunk_id": chunk_info.get("chunk_id"),
                }
            )

        episode_uuids = [episode.uuid for episode in bulk_result.episodes]
        created = await graphiti.get_nodes_and_edges_by_episode(episode_uuids)

        logger.info(
            "Graphiti ingest bulk completed "
            f"document_id={document_id} "
            f"group_id={effective_group_id} "
            f"episodes={len(bulk_result.episodes)} "
            f"created_nodes={len(bulk_result.nodes)} "
            f"created_edges={len(bulk_result.edges)}"
        )

        return {
            "document_id": document_id,
            "document_name": document_name,
            "group_id": effective_group_id,
            "chunk_count": len(chunks),
            "episodes": episode_results,
            "created_counts": {
                "episodic_edges": len(bulk_result.episodic_edges),
                "nodes": len(bulk_result.nodes),
                "edges": len(bulk_result.edges),
                "communities": len(bulk_result.communities),
                "community_edges": len(bulk_result.community_edges),
            },
            "queried_counts": {
                "nodes": len(created.nodes),
                "edges": len(created.edges),
                "episodes": len(created.episodes),
                "communities": len(created.communities),
            },
            "node_preview": [
                {
                    "uuid": node.uuid,
                    "name": node.name,
                    "summary": (node.summary or "")[:200],
                }
                for node in created.nodes[:10]
            ],
            "edge_preview": [
                {
                    "uuid": edge.uuid,
                    "fact": edge.fact,
                }
                for edge in created.edges[:10]
            ],
        }

    @staticmethod
    def _build_chunk_source_description(
        *,
        base_description: str,
        document_id: str,
        chunk_id: str,
        source: str,
        metadata: dict[str, Any],
    ) -> str:
        metadata_parts = [f"{key}={value}" for key, value in metadata.items()]
        description_parts = [
            base_description,
            f"document_id={document_id}",
            f"chunk_id={chunk_id}",
            f"source={source}",
        ]
        if metadata_parts:
            description_parts.append("metadata=" + ", ".join(metadata_parts))
        return " | ".join(description_parts)

    @staticmethod
    def _sanitize_group_token(value: Any, fallback: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "")).strip("-")
        if not normalized:
            normalized = fallback
        return normalized

    @classmethod
    def _build_document_group_id(cls, document_id: str) -> str:
        return f"document-{cls._sanitize_group_token(document_id, 'unknown-document')}"

    @classmethod
    def _build_group_id(cls, *, document_id: str, metadata: dict[str, Any]) -> str:
        organization_id = str(metadata.get("organization_id") or "").strip()
        if organization_id:
            return f"org-{cls._sanitize_group_token(organization_id, 'unknown-organization')}"
        return cls._build_document_group_id(document_id)

    @staticmethod
    def _coerce_optional_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def _parse_source_description(cls, source_description: str | None) -> dict[str, str]:
        parsed: dict[str, str] = {}
        if not source_description:
            return parsed

        parts = [part.strip() for part in str(source_description).split("|") if part.strip()]
        for part in parts:
            if part.startswith("metadata="):
                metadata_text = part[len("metadata="):].strip()
                for item in metadata_text.split(","):
                    if "=" not in item:
                        continue
                    key, value = item.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        parsed[key] = value
                continue

            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                parsed[key] = value

        return parsed

    @staticmethod
    def _parse_episode_name(episode_name: str | None) -> tuple[str | None, str | None]:
        if not episode_name:
            return None, None
        if "::" not in episode_name:
            return episode_name, None
        document_name, chunk_id = episode_name.rsplit("::", 1)
        return document_name or None, chunk_id or None

    async def _get_episode_record_for_node(self, *, node_uuid: str, group_id: str | None) -> dict[str, Any] | None:
        graphiti = self._require_graphiti()
        group_filter = "WHERE episode.group_id = $group_id" if group_id else ""
        query = f"""
            MATCH (episode:Episodic)-[:MENTIONS]->(:Entity {{uuid: $node_uuid}})
            {group_filter}
            RETURN
                episode.uuid AS uuid,
                episode.name AS name,
                episode.group_id AS group_id,
                episode.source_description AS source_description,
                episode.content AS content,
                episode.created_at AS created_at,
                episode.valid_at AS valid_at
            ORDER BY episode.valid_at DESC, episode.created_at DESC
            LIMIT 1
        """
        records, _, _ = await graphiti.driver.execute_query(
            query,
            node_uuid=node_uuid,
            group_id=group_id,
            routing_="r",
        )
        if not records:
            return None
        return dict(records[0])

    async def _get_episode_records_by_uuids(self, episode_uuids: list[str]) -> list[dict[str, Any]]:
        if not episode_uuids:
            return []
        graphiti = self._require_graphiti()
        records, _, _ = await graphiti.driver.execute_query(
            """
            MATCH (episode:Episodic)
            WHERE episode.uuid IN $episode_uuids
            RETURN
                episode.uuid AS uuid,
                episode.name AS name,
                episode.group_id AS group_id,
                episode.source_description AS source_description,
                episode.content AS content,
                episode.created_at AS created_at,
                episode.valid_at AS valid_at
            ORDER BY episode.valid_at DESC, episode.created_at DESC
            """,
            episode_uuids=episode_uuids,
            routing_="r",
        )
        return [dict(record) for record in records]

    def _build_episode_provenance(self, episode_record: dict[str, Any] | None) -> dict[str, Any]:
        if not episode_record:
            return {}

        source_description = self._coerce_optional_text(episode_record.get("source_description")) or ""
        parsed_description = self._parse_source_description(source_description)
        fallback_document_name, fallback_chunk_id = self._parse_episode_name(
            self._coerce_optional_text(episode_record.get("name"))
        )
        content = self._coerce_optional_text(episode_record.get("content")) or ""
        document_name = (
            parsed_description.get("document_name")
            or fallback_document_name
            or "Graph episode"
        )
        chunk_id = parsed_description.get("chunk_id") or fallback_chunk_id
        document_id = (
            parsed_description.get("document_id")
            or self._coerce_optional_text(episode_record.get("uuid"))
            or document_name
        )
        snippet = content[: self.SEARCH_SNIPPET_LIMIT]

        return {
            "episode_uuid": self._coerce_optional_text(episode_record.get("uuid")),
            "episode_name": self._coerce_optional_text(episode_record.get("name")),
            "group_id": self._coerce_optional_text(episode_record.get("group_id")),
            "document_id": document_id,
            "document_name": document_name,
            "file_name": document_name,
            "source_url": parsed_description.get("source_url") or "",
            "chunk_id": chunk_id,
            "organization_id": parsed_description.get("organization_id"),
            "content_text": content[: self.SEARCH_CONTENT_PREVIEW_LIMIT],
            "snippet": snippet,
        }

    def _build_node_hit(
        self,
        *,
        node,
        score: float | None,
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        summary = (getattr(node, "summary", None) or "").strip()
        content_text = provenance.get("content_text") or summary
        snippet = provenance.get("snippet") or content_text[: self.SEARCH_SNIPPET_LIMIT]
        document_name = provenance.get("document_name") or node.name
        document_id = provenance.get("document_id") or node.uuid
        source_url = provenance.get("source_url") or ""
        chunk_id = provenance.get("chunk_id")

        return {
            "uuid": node.uuid,
            "name": node.name,
            "summary": summary[:500],
            "labels": list(node.labels) if node.labels else [],
            "created_at": node.created_at,
            "score": score,
            "hit_type": "node",
            "group_id": provenance.get("group_id") or getattr(node, "group_id", None),
            "episode_uuid": provenance.get("episode_uuid"),
            "episode_name": provenance.get("episode_name"),
            "document_id": document_id,
            "document_name": document_name,
            "file_name": document_name,
            "source_url": source_url,
            "chunk_id": chunk_id,
            "content_text": content_text,
            "snippet": snippet,
        }

    def _build_fact_hit(
        self,
        *,
        edge,
        score: float | None,
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        document_name = provenance.get("document_name") or getattr(edge, "name", None) or "Graph fact"
        document_id = provenance.get("document_id") or edge.uuid
        source_url = provenance.get("source_url") or ""
        chunk_id = provenance.get("chunk_id")
        content_text = provenance.get("content_text") or getattr(edge, "fact", None) or ""
        snippet = provenance.get("snippet") or content_text[: self.SEARCH_SNIPPET_LIMIT]

        return {
            "uuid": edge.uuid,
            "name": getattr(edge, "name", None),
            "fact": getattr(edge, "fact", None),
            "valid_at": getattr(edge, "valid_at", None),
            "invalid_at": getattr(edge, "invalid_at", None),
            "source_node_uuid": getattr(edge, "source_node_uuid", None),
            "target_node_uuid": getattr(edge, "target_node_uuid", None),
            "score": score,
            "hit_type": "fact",
            "group_id": provenance.get("group_id") or getattr(edge, "group_id", None),
            "episode_uuid": provenance.get("episode_uuid"),
            "episode_name": provenance.get("episode_name"),
            "document_id": document_id,
            "document_name": document_name,
            "file_name": document_name,
            "source_url": source_url,
            "chunk_id": chunk_id,
            "content_text": content_text,
            "snippet": snippet,
        }

    async def search_nodes(
        self,
        *,
        query: str,
        limit: int = 10,
        group_id: str | None = None,
    ) -> list[dict[str, Any]]:
        await self.ensure_schema()
        graphiti = self._require_graphiti()

        search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        search_config.limit = limit
        group_ids = [group_id] if group_id else None

        results = await graphiti.search_(  # type: ignore[attr-defined]
            query=query,
            config=search_config,
            group_ids=group_ids,
        )

        node_scores = list(getattr(results, "node_reranker_scores", []) or [])
        nodes = []
        for index, node in enumerate(getattr(results, "nodes", []) or []):
            score = node_scores[index] if index < len(node_scores) else None
            provenance = self._build_episode_provenance(
                await self._get_episode_record_for_node(node_uuid=node.uuid, group_id=group_id)
            )
            nodes.append(self._build_node_hit(node=node, score=score, provenance=provenance))
        return nodes

    async def search_facts(
        self,
        *,
        query: str,
        limit: int = 10,
        center_node_uuid: str | None = None,
        group_id: str | None = None,
    ) -> list[dict[str, Any]]:
        await self.ensure_schema()
        graphiti = self._require_graphiti()
        group_ids = [group_id] if group_id else None

        search_config = (
            EDGE_HYBRID_SEARCH_NODE_DISTANCE if center_node_uuid is not None else EDGE_HYBRID_SEARCH_RRF
        )
        search_config = search_config.model_copy(deep=True)
        search_config.limit = limit

        results = await graphiti.search_(
            query=query,
            config=search_config,
            group_ids=group_ids,
            center_node_uuid=center_node_uuid,
        )

        edge_scores = list(getattr(results, "edge_reranker_scores", []) or [])
        facts = []
        for index, edge in enumerate(getattr(results, "edges", []) or []):
            score = edge_scores[index] if index < len(edge_scores) else None
            episode_records = await self._get_episode_records_by_uuids(list(getattr(edge, "episodes", []) or []))
            provenance = self._build_episode_provenance(episode_records[0] if episode_records else None)
            facts.append(self._build_fact_hit(edge=edge, score=score, provenance=provenance))
        return facts

    async def get_graph_stats(self) -> dict[str, int]:
        await self.ensure_schema()
        graphiti = self._require_graphiti()
        driver = graphiti.driver

        async with driver.session() as session:
            entity_result = await session.run("MATCH (n:Entity) RETURN count(n) AS count")
            entity_record = await entity_result.single()

            edge_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            edge_record = await edge_result.single()

            episode_result = await session.run("MATCH (n:Episodic) RETURN count(n) AS count")
            episode_record = await episode_result.single()

        return {
            "entity_count": int(entity_record["count"]) if entity_record else 0,
            "edge_count": int(edge_record["count"]) if edge_record else 0,
            "episode_count": int(episode_record["count"]) if episode_record else 0,
        }

    async def get_document_graph(self, document_id: str, *, limit: int = 80) -> dict[str, Any]:
        group_id = self._build_safe_group_id(document_id)
        graph = await self.get_groups_graph([group_id], limit=limit)

        return {
            "document_id": document_id,
            "group_id": group_id,
            **graph,
        }

    async def get_documents_graph(
        self,
        document_ids: list[str],
        *,
        scope_id: str = "documents",
        limit: int = 160,
    ) -> dict[str, Any]:
        group_ids = [self._build_safe_group_id(document_id) for document_id in document_ids if document_id]
        graph = await self.get_groups_graph(group_ids, limit=limit)

        return {
            "document_id": scope_id,
            "group_id": ",".join(group_ids),
            "document_ids": document_ids,
            **graph,
        }

    async def get_groups_graph(self, group_ids: list[str], *, limit: int = 160) -> dict[str, Any]:
        await self.ensure_schema()
        graphiti = self._require_graphiti()
        driver = graphiti.driver
        safe_group_ids = [group_id for group_id in group_ids if group_id]

        if not safe_group_ids:
            return {
                "nodes": [],
                "edges": [],
                "episodes": [],
                "counts": {
                    "nodes": 0,
                    "edges": 0,
                    "episodes": 0,
                },
            }

        async with driver.session() as session:
            nodes_result = await session.run(
                """
                MATCH (n)
                WHERE n.group_id IN $group_ids AND NOT n:Episodic
                RETURN n.uuid AS id,
                       coalesce(n.name, n.uuid) AS label,
                       coalesce(n.summary, '') AS summary,
                       labels(n) AS labels,
                       n.group_id AS group_id
                LIMIT $limit
                """,
                {"group_ids": safe_group_ids, "limit": limit},
            )
            nodes = [record.data() async for record in nodes_result]

            edges_result = await session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE a.group_id IN $group_ids
                  AND b.group_id IN $group_ids
                  AND NOT a:Episodic
                  AND NOT b:Episodic
                RETURN coalesce(r.uuid, elementId(r)) AS id,
                       a.uuid AS source,
                       b.uuid AS target,
                       type(r) AS type,
                       coalesce(r.fact, r.name, '') AS label,
                       coalesce(a.group_id, b.group_id, '') AS group_id
                LIMIT $limit
                """,
                {"group_ids": safe_group_ids, "limit": limit * 2},
            )
            edges = [record.data() async for record in edges_result]

            episodes_result = await session.run(
                """
                MATCH (e:Episodic)
                WHERE e.group_id IN $group_ids
                RETURN e.uuid AS id,
                       coalesce(e.name, e.uuid) AS label,
                       coalesce(e.source_description, '') AS source_description,
                       e.group_id AS group_id
                LIMIT $limit
                """,
                {"group_ids": safe_group_ids, "limit": limit},
            )
            episodes = [record.data() async for record in episodes_result]

        return {
            "nodes": nodes,
            "edges": edges,
            "episodes": episodes,
            "counts": {
                "nodes": len(nodes),
                "edges": len(edges),
                "episodes": len(episodes),
            },
        }

    async def close(self) -> None:
        if self.graphiti is not None and hasattr(self.graphiti, "close"):
            await self.graphiti.close()
        self.graphiti = None
        self._initialized = False
        self._schema_ready = False

    def _require_graphiti(self) -> Graphiti:
        if self.graphiti is None:
            raise ValueError("Graphiti is not initialized")
        return self.graphiti


_graphiti_services: dict[int, GraphitiService] = {}
_graphiti_services_lock = threading.Lock()


async def get_graphiti_service() -> GraphitiService:
    current_loop_id = id(asyncio.get_running_loop())
    with _graphiti_services_lock:
        existing_service = _graphiti_services.get(current_loop_id)
    if existing_service is not None:
        return existing_service

    new_service = GraphitiService()
    await new_service.initialize()

    with _graphiti_services_lock:
        existing_service = _graphiti_services.get(current_loop_id)
        if existing_service is None:
            _graphiti_services[current_loop_id] = new_service
            return new_service

    await new_service.close()
    return existing_service
