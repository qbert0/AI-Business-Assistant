from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.utils.benchmark_pdf import TextChunk, build_chunks_for_report, discover_reports
from scripts.utils.benchmark_qa import (
    answer_with_rag,
    answer_with_ras,
    load_benchmark_questions,
    run_rag_benchmark,
    run_ras_benchmark,
    write_benchmark_results,
)
from scripts.utils.config_loader import get_nested, load_config
from scripts.utils.graph_status import (
    get_neo4j_namespace_status,
    get_redis_ingest_status,
    wait_for_graph_idle,
)
from scripts.utils.neo4j_maintenance import purge_graph_namespace
from scripts.utils.rag_index import ingest_graph
from scripts.utils.redis_maintenance import delete_stream
from scripts.utils.vector_index import create_embeddings, delete_elasticsearch_index, index_elasticsearch


DEFAULT_CONFIG_PATH = "scripts/configs/config.yml"


def cfg(config: dict[str, Any], path: str, default: Any = None) -> Any:
    return get_nested(config, path, default)


def env_or_config(env_name: str, config: dict[str, Any], path: str, default: Any = None) -> Any:
    value = os.getenv(env_name)
    return value if value not in (None, "") else cfg(config, path, default)


def write_manifest(chunks: list[TextChunk], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    documents: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        documents.setdefault(
            chunk.document_id,
            {
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "chunk_count": 0,
            },
        )["chunk_count"] += 1
    payload = {
        "documents": list(documents.values()),
        "chunk_count": len(chunks),
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest written: {output_path}")


def add_benchmark_parser(subparsers: argparse._SubParsersAction) -> None:
    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark utilities")
    benchmark_subparsers = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)

    index_parser = benchmark_subparsers.add_parser("index", help="Index benchmark PDF reports")
    index_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    index_parser.add_argument("--mode", choices=["vector", "graph", "both"], default="vector")
    index_parser.add_argument("--reports-glob")
    index_parser.add_argument("--limit", type=int)
    index_parser.add_argument("--dry-run", action="store_true")
    index_parser.add_argument("--manifest")

    index_parser.add_argument("--chunk-chars", type=int)
    index_parser.add_argument("--chunk-overlap", type=int)
    index_parser.add_argument("--document-namespace")
    index_parser.add_argument("--organization-id")
    index_parser.add_argument("--no-reset", action="store_true", help="Do not clean benchmark indexes before indexing")
    index_parser.add_argument("--request-timeout", type=float)
    index_parser.add_argument("--request-retries", type=int)

    index_parser.add_argument("--model-service-url")
    index_parser.add_argument("--embedding-model-id")
    index_parser.add_argument("--embedding-use-case")
    index_parser.add_argument("--embedding-dimensions", type=int)
    index_parser.add_argument("--embedding-batch-size", type=int)

    index_parser.add_argument("--elasticsearch-url")
    index_parser.add_argument("--elasticsearch-username")
    index_parser.add_argument("--elasticsearch-password")
    index_parser.add_argument("--elasticsearch-verify-certs", action="store_true")
    index_parser.add_argument("--index-name")
    index_parser.add_argument("--elasticsearch-batch-size", type=int)
    index_parser.add_argument("--recreate", action="store_true")

    index_parser.add_argument("--rag-url")
    index_parser.add_argument("--neo4j-uri")
    index_parser.add_argument("--neo4j-username")
    index_parser.add_argument("--neo4j-password")

    status_parser = benchmark_subparsers.add_parser("graph-status", help="Check benchmark graph ingest status")
    status_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    status_parser.add_argument("--document-namespace")
    status_parser.add_argument("--redis-host")
    status_parser.add_argument("--redis-port", type=int)
    status_parser.add_argument("--redis-db", type=int)
    status_parser.add_argument("--redis-password")
    status_parser.add_argument("--redis-queue")
    status_parser.add_argument("--redis-group")
    status_parser.add_argument("--neo4j-uri")
    status_parser.add_argument("--neo4j-username")
    status_parser.add_argument("--neo4j-password")
    status_parser.add_argument("--watch", action="store_true")
    status_parser.add_argument("--interval", type=float, default=10.0)
    status_parser.add_argument("--timeout", type=float, default=3600.0)

    clean_parser = benchmark_subparsers.add_parser("clean", help="Clean benchmark graph/vector state")
    clean_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    clean_parser.add_argument("--target", choices=["graph", "vector", "all"], default="graph")
    clean_parser.add_argument("--document-namespace")
    clean_parser.add_argument("--redis-host")
    clean_parser.add_argument("--redis-port", type=int)
    clean_parser.add_argument("--redis-db", type=int)
    clean_parser.add_argument("--redis-password")
    clean_parser.add_argument("--redis-queue")
    clean_parser.add_argument("--neo4j-uri")
    clean_parser.add_argument("--neo4j-username")
    clean_parser.add_argument("--neo4j-password")
    clean_parser.add_argument("--elasticsearch-url")
    clean_parser.add_argument("--elasticsearch-username")
    clean_parser.add_argument("--elasticsearch-password")
    clean_parser.add_argument("--elasticsearch-verify-certs", action="store_true")
    clean_parser.add_argument("--index-name")

    answer_parser = benchmark_subparsers.add_parser("answer", help="Answer a benchmark question with RAG or RAS")
    answer_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    answer_parser.add_argument("--strategy", choices=["rag", "ras"], default="rag")
    answer_parser.add_argument("--question", required=True)
    answer_parser.add_argument("--output")
    answer_parser.add_argument("--keep-query-graph", action="store_true")

    answer_parser.add_argument("--organization-id")
    answer_parser.add_argument("--request-timeout", type=float)
    answer_parser.add_argument("--request-retries", type=int)
    answer_parser.add_argument("--model-service-url")
    answer_parser.add_argument("--embedding-model-id")
    answer_parser.add_argument("--embedding-use-case")
    answer_parser.add_argument("--embedding-dimensions", type=int)
    answer_parser.add_argument("--llm-model-id")
    answer_parser.add_argument("--llm-use-case")
    answer_parser.add_argument("--llm-temperature", type=float)
    answer_parser.add_argument("--answer-max-tokens", type=int)
    answer_parser.add_argument("--analysis-max-tokens", type=int)
    answer_parser.add_argument("--elasticsearch-url")
    answer_parser.add_argument("--elasticsearch-username")
    answer_parser.add_argument("--elasticsearch-password")
    answer_parser.add_argument("--elasticsearch-verify-certs", action="store_true")
    answer_parser.add_argument("--index-name")
    answer_parser.add_argument("--top-k", type=int)
    answer_parser.add_argument("--num-candidates", type=int)
    answer_parser.add_argument("--max-rounds", type=int)
    answer_parser.add_argument("--max-follow-up-queries", type=int)
    answer_parser.add_argument("--neo4j-uri")
    answer_parser.add_argument("--neo4j-username")
    answer_parser.add_argument("--neo4j-password")
    answer_parser.add_argument("--query-graph-namespace")

    run_rag_parser = benchmark_subparsers.add_parser("run-rag", help="Run basic one-shot RAG benchmark from Excel")
    run_rag_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    run_rag_parser.add_argument("--dataset")
    run_rag_parser.add_argument("--output")
    run_rag_parser.add_argument("--limit", type=int)
    run_rag_parser.add_argument("--organization-id")
    run_rag_parser.add_argument("--request-timeout", type=float)
    run_rag_parser.add_argument("--request-retries", type=int)
    run_rag_parser.add_argument("--model-service-url")
    run_rag_parser.add_argument("--embedding-model-id")
    run_rag_parser.add_argument("--embedding-use-case")
    run_rag_parser.add_argument("--embedding-dimensions", type=int)
    run_rag_parser.add_argument("--llm-model-id")
    run_rag_parser.add_argument("--llm-use-case")
    run_rag_parser.add_argument("--llm-temperature", type=float)
    run_rag_parser.add_argument("--answer-max-tokens", type=int)
    run_rag_parser.add_argument("--elasticsearch-url")
    run_rag_parser.add_argument("--elasticsearch-username")
    run_rag_parser.add_argument("--elasticsearch-password")
    run_rag_parser.add_argument("--elasticsearch-verify-certs", action="store_true")
    run_rag_parser.add_argument("--index-name")
    run_rag_parser.add_argument("--top-k", type=int)
    run_rag_parser.add_argument("--num-candidates", type=int)

    run_ras_parser = benchmark_subparsers.add_parser("run-ras", help="Run iterative RAS benchmark from Excel")
    run_ras_parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    run_ras_parser.add_argument("--dataset")
    run_ras_parser.add_argument("--output")
    run_ras_parser.add_argument("--limit", type=int)
    run_ras_parser.add_argument("--keep-query-graph", action="store_true")
    run_ras_parser.add_argument("--organization-id")
    run_ras_parser.add_argument("--request-timeout", type=float)
    run_ras_parser.add_argument("--request-retries", type=int)
    run_ras_parser.add_argument("--model-service-url")
    run_ras_parser.add_argument("--embedding-model-id")
    run_ras_parser.add_argument("--embedding-use-case")
    run_ras_parser.add_argument("--embedding-dimensions", type=int)
    run_ras_parser.add_argument("--llm-model-id")
    run_ras_parser.add_argument("--llm-use-case")
    run_ras_parser.add_argument("--llm-temperature", type=float)
    run_ras_parser.add_argument("--answer-max-tokens", type=int)
    run_ras_parser.add_argument("--analysis-max-tokens", type=int)
    run_ras_parser.add_argument("--elasticsearch-url")
    run_ras_parser.add_argument("--elasticsearch-username")
    run_ras_parser.add_argument("--elasticsearch-password")
    run_ras_parser.add_argument("--elasticsearch-verify-certs", action="store_true")
    run_ras_parser.add_argument("--index-name")
    run_ras_parser.add_argument("--top-k", type=int)
    run_ras_parser.add_argument("--num-candidates", type=int)
    run_ras_parser.add_argument("--max-rounds", type=int)
    run_ras_parser.add_argument("--max-follow-up-queries", type=int)
    run_ras_parser.add_argument("--neo4j-uri")
    run_ras_parser.add_argument("--neo4j-username")
    run_ras_parser.add_argument("--neo4j-password")
    run_ras_parser.add_argument("--query-graph-namespace")


def resolve_index_options(args: argparse.Namespace) -> argparse.Namespace:
    config = load_config(args.config)
    args.reports_glob = args.reports_glob or cfg(config, "benchmark.reports_glob", "benchmark/dataset/reports/*.pdf")
    args.manifest = args.manifest or cfg(config, "benchmark.manifest_path", "benchmark/results/index_manifest.json")
    args.chunk_chars = args.chunk_chars or int(cfg(config, "benchmark.chunking.chunk_chars", 3500))
    args.chunk_overlap = args.chunk_overlap or int(cfg(config, "benchmark.chunking.chunk_overlap", 400))
    args.document_namespace = args.document_namespace or cfg(config, "benchmark.document_namespace", "benchmark")
    args.organization_id = args.organization_id or env_or_config("BENCHMARK_ORGANIZATION_ID", config, "benchmark.organization_id", "benchmark")
    args.reset_before_index = (not args.no_reset) and bool(cfg(config, "benchmark.reset_before_index", True))
    args.request_timeout = args.request_timeout or float(env_or_config("BENCHMARK_REQUEST_TIMEOUT", config, "benchmark.request.timeout_seconds", 180))
    args.request_retries = args.request_retries if args.request_retries is not None else int(env_or_config("BENCHMARK_REQUEST_RETRIES", config, "benchmark.request.retries", 1))

    args.model_service_url = args.model_service_url or env_or_config("BENCHMARK_MODEL_SERVICE_URL", config, "benchmark.model_service.url", "http://localhost:8888")
    args.embedding_model_id = args.embedding_model_id or env_or_config("BENCHMARK_EMBEDDING_MODEL_ID", config, "benchmark.model_service.embedding_model_id")
    args.embedding_use_case = args.embedding_use_case or env_or_config("BENCHMARK_EMBEDDING_USE_CASE", config, "benchmark.model_service.embedding_use_case", "embeddings")
    args.embedding_dimensions = args.embedding_dimensions if args.embedding_dimensions is not None else cfg(config, "benchmark.model_service.embedding_dimensions")
    args.embedding_batch_size = args.embedding_batch_size or int(cfg(config, "benchmark.model_service.embedding_batch_size", 8))

    args.elasticsearch_url = args.elasticsearch_url or env_or_config("BENCHMARK_ELASTICSEARCH_URL", config, "benchmark.elasticsearch.url", "http://localhost:9200")
    args.elasticsearch_username = args.elasticsearch_username or env_or_config("BENCHMARK_ELASTICSEARCH_USERNAME", config, "benchmark.elasticsearch.username")
    args.elasticsearch_password = args.elasticsearch_password or env_or_config("BENCHMARK_ELASTICSEARCH_PASSWORD", config, "benchmark.elasticsearch.password")
    args.elasticsearch_verify_certs = args.elasticsearch_verify_certs or bool(cfg(config, "benchmark.elasticsearch.verify_certs", False))
    args.index_name = args.index_name or env_or_config("BENCHMARK_ELASTICSEARCH_INDEX", config, "benchmark.elasticsearch.index_name", "benchmark_vector")
    args.elasticsearch_batch_size = args.elasticsearch_batch_size or int(cfg(config, "benchmark.elasticsearch.batch_size", 128))
    args.recreate = args.recreate or (args.reset_before_index and bool(cfg(config, "benchmark.elasticsearch.recreate", True)))

    args.rag_url = args.rag_url or env_or_config("BENCHMARK_RAG_URL", config, "benchmark.rag.url", "http://localhost:8003")
    args.neo4j_uri = getattr(args, "neo4j_uri", None) or env_or_config("BENCHMARK_NEO4J_URI", config, "benchmark.neo4j.uri", "bolt://localhost:7687")
    args.neo4j_username = getattr(args, "neo4j_username", None) or env_or_config("BENCHMARK_NEO4J_USERNAME", config, "benchmark.neo4j.username", "neo4j")
    args.neo4j_password = getattr(args, "neo4j_password", None) or env_or_config("BENCHMARK_NEO4J_PASSWORD", config, "benchmark.neo4j.password", "pleaseletmein")
    return args


def resolve_graph_status_options(args: argparse.Namespace) -> argparse.Namespace:
    config = load_config(args.config)
    args.document_namespace = args.document_namespace or cfg(config, "benchmark.document_namespace", "benchmark")
    args.redis_host = args.redis_host or env_or_config("BENCHMARK_REDIS_HOST", config, "benchmark.redis.host", "localhost")
    args.redis_port = args.redis_port or int(env_or_config("BENCHMARK_REDIS_PORT", config, "benchmark.redis.port", 6379))
    args.redis_db = args.redis_db if args.redis_db is not None else int(env_or_config("BENCHMARK_REDIS_DB", config, "benchmark.redis.db", 0))
    args.redis_password = args.redis_password or env_or_config("BENCHMARK_REDIS_PASSWORD", config, "benchmark.redis.password")
    args.redis_queue = args.redis_queue or env_or_config("BENCHMARK_REDIS_QUEUE", config, "benchmark.redis.ingest_queue", "rag-ingest")
    args.redis_group = args.redis_group or env_or_config("BENCHMARK_REDIS_GROUP", config, "benchmark.redis.ingest_group", "rag-ingest")
    args.neo4j_uri = getattr(args, "neo4j_uri", None) or env_or_config("BENCHMARK_NEO4J_URI", config, "benchmark.neo4j.uri", "bolt://localhost:7687")
    args.neo4j_username = getattr(args, "neo4j_username", None) or env_or_config("BENCHMARK_NEO4J_USERNAME", config, "benchmark.neo4j.username", "neo4j")
    args.neo4j_password = getattr(args, "neo4j_password", None) or env_or_config("BENCHMARK_NEO4J_PASSWORD", config, "benchmark.neo4j.password", "pleaseletmein")
    return args


def resolve_clean_options(args: argparse.Namespace) -> argparse.Namespace:
    config = load_config(args.config)
    args.document_namespace = args.document_namespace or cfg(config, "benchmark.document_namespace", "benchmark")
    args.redis_host = args.redis_host or env_or_config("BENCHMARK_REDIS_HOST", config, "benchmark.redis.host", "localhost")
    args.redis_port = args.redis_port or int(env_or_config("BENCHMARK_REDIS_PORT", config, "benchmark.redis.port", 6379))
    args.redis_db = args.redis_db if args.redis_db is not None else int(env_or_config("BENCHMARK_REDIS_DB", config, "benchmark.redis.db", 0))
    args.redis_password = args.redis_password or env_or_config("BENCHMARK_REDIS_PASSWORD", config, "benchmark.redis.password")
    args.redis_queue = args.redis_queue or env_or_config("BENCHMARK_REDIS_QUEUE", config, "benchmark.redis.ingest_queue", "rag-ingest")
    args.neo4j_uri = getattr(args, "neo4j_uri", None) or env_or_config("BENCHMARK_NEO4J_URI", config, "benchmark.neo4j.uri", "bolt://localhost:7687")
    args.neo4j_username = getattr(args, "neo4j_username", None) or env_or_config("BENCHMARK_NEO4J_USERNAME", config, "benchmark.neo4j.username", "neo4j")
    args.neo4j_password = getattr(args, "neo4j_password", None) or env_or_config("BENCHMARK_NEO4J_PASSWORD", config, "benchmark.neo4j.password", "pleaseletmein")
    args.elasticsearch_url = args.elasticsearch_url or env_or_config("BENCHMARK_ELASTICSEARCH_URL", config, "benchmark.elasticsearch.url", "http://localhost:9200")
    args.elasticsearch_username = args.elasticsearch_username or env_or_config("BENCHMARK_ELASTICSEARCH_USERNAME", config, "benchmark.elasticsearch.username")
    args.elasticsearch_password = args.elasticsearch_password or env_or_config("BENCHMARK_ELASTICSEARCH_PASSWORD", config, "benchmark.elasticsearch.password")
    args.elasticsearch_verify_certs = args.elasticsearch_verify_certs or bool(cfg(config, "benchmark.elasticsearch.verify_certs", False))
    args.index_name = args.index_name or env_or_config("BENCHMARK_ELASTICSEARCH_INDEX", config, "benchmark.elasticsearch.index_name", "benchmark_vector")
    return args


def resolve_answer_options(args: argparse.Namespace) -> argparse.Namespace:
    config = load_config(args.config)
    args.organization_id = args.organization_id or env_or_config("BENCHMARK_ORGANIZATION_ID", config, "benchmark.organization_id", "benchmark")
    args.request_timeout = args.request_timeout or float(env_or_config("BENCHMARK_REQUEST_TIMEOUT", config, "benchmark.request.timeout_seconds", 180))
    args.request_retries = args.request_retries if args.request_retries is not None else int(env_or_config("BENCHMARK_REQUEST_RETRIES", config, "benchmark.request.retries", 1))

    args.model_service_url = args.model_service_url or env_or_config("BENCHMARK_MODEL_SERVICE_URL", config, "benchmark.model_service.url", "http://localhost:8888")
    args.embedding_model_id = args.embedding_model_id or env_or_config("BENCHMARK_EMBEDDING_MODEL_ID", config, "benchmark.model_service.embedding_model_id")
    args.embedding_use_case = args.embedding_use_case or env_or_config("BENCHMARK_EMBEDDING_USE_CASE", config, "benchmark.model_service.embedding_use_case", "embeddings")
    args.embedding_dimensions = args.embedding_dimensions if args.embedding_dimensions is not None else cfg(config, "benchmark.model_service.embedding_dimensions")
    args.llm_model_id = args.llm_model_id or env_or_config("BENCHMARK_LLM_MODEL_ID", config, "benchmark.qa.llm_model_id")
    args.llm_use_case = args.llm_use_case or env_or_config("BENCHMARK_LLM_USE_CASE", config, "benchmark.qa.llm_use_case", "chat_advisory")
    args.llm_temperature = args.llm_temperature if args.llm_temperature is not None else float(cfg(config, "benchmark.qa.temperature", 0.1))
    args.answer_max_tokens = args.answer_max_tokens or int(cfg(config, "benchmark.qa.answer_max_tokens", 2048))
    args.analysis_max_tokens = getattr(args, "analysis_max_tokens", None) or int(cfg(config, "benchmark.qa.analysis_max_tokens", 1200))

    args.elasticsearch_url = args.elasticsearch_url or env_or_config("BENCHMARK_ELASTICSEARCH_URL", config, "benchmark.elasticsearch.url", "http://localhost:9200")
    args.elasticsearch_username = args.elasticsearch_username or env_or_config("BENCHMARK_ELASTICSEARCH_USERNAME", config, "benchmark.elasticsearch.username")
    args.elasticsearch_password = args.elasticsearch_password or env_or_config("BENCHMARK_ELASTICSEARCH_PASSWORD", config, "benchmark.elasticsearch.password")
    args.elasticsearch_verify_certs = args.elasticsearch_verify_certs or bool(cfg(config, "benchmark.elasticsearch.verify_certs", False))
    args.index_name = args.index_name or env_or_config("BENCHMARK_ELASTICSEARCH_INDEX", config, "benchmark.elasticsearch.index_name", "benchmark_vector")
    args.top_k = args.top_k or int(cfg(config, "benchmark.qa.top_k", 8))
    args.num_candidates = args.num_candidates or int(cfg(config, "benchmark.qa.num_candidates", 80))
    args.max_rounds = getattr(args, "max_rounds", None) or int(cfg(config, "benchmark.qa.max_rounds", 3))
    args.max_follow_up_queries = getattr(args, "max_follow_up_queries", None) or int(cfg(config, "benchmark.qa.max_follow_up_queries", 3))

    args.neo4j_uri = getattr(args, "neo4j_uri", None) or env_or_config("BENCHMARK_NEO4J_URI", config, "benchmark.neo4j.uri", "bolt://localhost:7687")
    args.neo4j_username = getattr(args, "neo4j_username", None) or env_or_config("BENCHMARK_NEO4J_USERNAME", config, "benchmark.neo4j.username", "neo4j")
    args.neo4j_password = getattr(args, "neo4j_password", None) or env_or_config("BENCHMARK_NEO4J_PASSWORD", config, "benchmark.neo4j.password", "pleaseletmein")
    args.query_graph_namespace = getattr(args, "query_graph_namespace", None) or cfg(config, "benchmark.qa.query_graph_namespace", "benchmark-query")
    args.cleanup_query_graph = (not getattr(args, "keep_query_graph", False)) and bool(cfg(config, "benchmark.qa.cleanup_query_graph", True))
    return args


def resolve_run_rag_options(args: argparse.Namespace) -> argparse.Namespace:
    args = resolve_answer_options(args)
    config = load_config(args.config)
    args.dataset = args.dataset or cfg(config, "benchmark.qa.dataset_path", "benchmark/dataset/benchmark_metric.xlsx")
    args.output = args.output or cfg(config, "benchmark.qa.rag_results_path", "benchmark/results/rag_results.xlsx")
    return args


def resolve_run_ras_options(args: argparse.Namespace) -> argparse.Namespace:
    args = resolve_answer_options(args)
    config = load_config(args.config)
    args.dataset = args.dataset or cfg(config, "benchmark.qa.dataset_path", "benchmark/dataset/benchmark_metric.xlsx")
    args.output = args.output or cfg(config, "benchmark.qa.ras_results_path", "benchmark/results/ras_basic_50.xlsx")
    return args


def run_benchmark_index(args: argparse.Namespace) -> int:
    args = resolve_index_options(args)
    if args.chunk_overlap >= args.chunk_chars:
        raise SystemExit("--chunk-overlap must be smaller than --chunk-chars")

    reports = discover_reports(args.reports_glob, args.limit)
    if not reports:
        raise SystemExit(f"No PDF reports found for pattern: {args.reports_glob}")

    print(f"found reports: {len(reports)}")
    chunks: list[TextChunk] = []
    for report in reports:
        pages, report_chunks = build_chunks_for_report(
            report,
            chunk_chars=args.chunk_chars,
            chunk_overlap=args.chunk_overlap,
            document_namespace=args.document_namespace,
        )
        chunks.extend(report_chunks)
        print(f"parsed {report.name}: pages={len(pages)} chunks={len(report_chunks)}")

    write_manifest(chunks, Path(args.manifest))
    if args.dry_run:
        print(f"dry-run complete: documents={len(reports)} chunks={len(chunks)}")
        return 0

    if args.mode in {"graph", "both"} and args.reset_before_index:
        purge_graph_namespace(
            uri=args.neo4j_uri,
            username=args.neo4j_username,
            password=args.neo4j_password,
            document_namespace=args.document_namespace,
        )

    if args.mode in {"vector", "both"}:
        vectors, _dimension = create_embeddings(
            chunks,
            model_service_url=args.model_service_url,
            organization_id=args.organization_id,
            model_id=args.embedding_model_id,
            use_case=args.embedding_use_case,
            dimensions=args.embedding_dimensions,
            batch_size=args.embedding_batch_size,
            timeout=args.request_timeout,
            retries=args.request_retries,
        )
        index_elasticsearch(
            chunks,
            vectors,
            url=args.elasticsearch_url,
            username=args.elasticsearch_username,
            password=args.elasticsearch_password,
            verify_certs=args.elasticsearch_verify_certs,
            index_name=args.index_name,
            batch_size=args.elasticsearch_batch_size,
            recreate=args.recreate,
        )

    if args.mode in {"graph", "both"}:
        ingest_graph(
            chunks,
            rag_url=args.rag_url,
            organization_id=args.organization_id,
            timeout=args.request_timeout,
            retries=args.request_retries,
        )

    return 0


def run_graph_status(args: argparse.Namespace) -> int:
    args = resolve_graph_status_options(args)
    redis_options = {
        "host": args.redis_host,
        "port": args.redis_port,
        "db": args.redis_db,
        "password": args.redis_password,
        "queue_name": args.redis_queue,
        "group_name": args.redis_group,
    }
    neo4j_options = {
        "uri": args.neo4j_uri,
        "username": args.neo4j_username,
        "password": args.neo4j_password,
        "document_namespace": args.document_namespace,
    }

    if args.watch:
        status = wait_for_graph_idle(
            redis_options=redis_options,
            neo4j_options=neo4j_options,
            interval_seconds=args.interval,
            timeout_seconds=args.timeout,
        )
    else:
        status = {
            "redis": get_redis_ingest_status(**redis_options),
            "neo4j": get_neo4j_namespace_status(**neo4j_options),
        }

    redis_status = status["redis"]
    neo4j_status = status["neo4j"]
    print(
        "redis "
        f"stream={redis_status.get('queue_name')} "
        f"length={redis_status.get('stream_length')} "
        f"pending={redis_status.get('pending')} "
        f"lag={redis_status.get('lag')} "
        f"last_delivered={redis_status.get('last_delivered_id')}"
    )
    print(
        "neo4j "
        f"group_prefix={neo4j_status.get('group_prefix')} "
        f"groups={neo4j_status.get('group_count')} "
        f"nodes={neo4j_status.get('node_count')} "
        f"edges={neo4j_status.get('edge_count')}"
    )
    for group in neo4j_status.get("groups", [])[:12]:
        print(f"neo4j_group {group.get('group_id')} nodes={group.get('node_count')}")
    return 0


def run_benchmark_clean(args: argparse.Namespace) -> int:
    args = resolve_clean_options(args)
    if args.target in {"graph", "all"}:
        delete_stream(
            host=args.redis_host,
            port=args.redis_port,
            db=args.redis_db,
            password=args.redis_password,
            queue_name=args.redis_queue,
        )
        purge_graph_namespace(
            uri=args.neo4j_uri,
            username=args.neo4j_username,
            password=args.neo4j_password,
            document_namespace=args.document_namespace,
        )

    if args.target in {"vector", "all"}:
        delete_elasticsearch_index(
            url=args.elasticsearch_url,
            username=args.elasticsearch_username,
            password=args.elasticsearch_password,
            verify_certs=args.elasticsearch_verify_certs,
            index_name=args.index_name,
        )
    return 0


def run_benchmark_answer(args: argparse.Namespace) -> int:
    args = resolve_answer_options(args)
    common = {
        "question": args.question,
        "model_service_url": args.model_service_url,
        "organization_id": args.organization_id,
        "embedding_model_id": args.embedding_model_id,
        "embedding_use_case": args.embedding_use_case,
        "embedding_dimensions": args.embedding_dimensions,
        "llm_model_id": args.llm_model_id,
        "llm_use_case": args.llm_use_case,
        "elasticsearch_url": args.elasticsearch_url,
        "elasticsearch_username": args.elasticsearch_username,
        "elasticsearch_password": args.elasticsearch_password,
        "elasticsearch_verify_certs": args.elasticsearch_verify_certs,
        "index_name": args.index_name,
        "top_k": args.top_k,
        "num_candidates": args.num_candidates,
        "answer_max_tokens": args.answer_max_tokens,
        "temperature": args.llm_temperature,
        "timeout": args.request_timeout,
        "retries": args.request_retries,
    }
    if args.strategy == "rag":
        result = answer_with_rag(**common)
    else:
        result = answer_with_ras(
            **common,
            max_rounds=args.max_rounds,
            max_follow_up_queries=args.max_follow_up_queries,
            analysis_max_tokens=args.analysis_max_tokens,
            neo4j_uri=args.neo4j_uri,
            neo4j_username=args.neo4j_username,
            neo4j_password=args.neo4j_password,
            query_graph_namespace=args.query_graph_namespace,
            cleanup_query_graph=args.cleanup_query_graph,
        )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"answer written: {output_path}")

    print("\nANSWER\n")
    print(result["answer"])
    print(f"\nevidence={len(result.get('evidence', []))} strategy={result.get('strategy')}")
    if result.get("query_graph_id"):
        print(f"query_graph_id={result['query_graph_id']}")
    return 0


def run_benchmark_rag_batch(args: argparse.Namespace) -> int:
    args = resolve_run_rag_options(args)
    questions = load_benchmark_questions(args.dataset, limit=args.limit)
    if not questions:
        raise SystemExit(f"No benchmark questions found in dataset: {args.dataset}")
    print(f"loaded benchmark questions: {len(questions)}")
    rows = run_rag_benchmark(
        questions,
        model_service_url=args.model_service_url,
        organization_id=args.organization_id,
        embedding_model_id=args.embedding_model_id,
        embedding_use_case=args.embedding_use_case,
        embedding_dimensions=args.embedding_dimensions,
        llm_model_id=args.llm_model_id,
        llm_use_case=args.llm_use_case,
        elasticsearch_url=args.elasticsearch_url,
        elasticsearch_username=args.elasticsearch_username,
        elasticsearch_password=args.elasticsearch_password,
        elasticsearch_verify_certs=args.elasticsearch_verify_certs,
        index_name=args.index_name,
        top_k=args.top_k,
        num_candidates=args.num_candidates,
        answer_max_tokens=args.answer_max_tokens,
        temperature=args.llm_temperature,
        timeout=args.request_timeout,
        retries=args.request_retries,
    )
    write_benchmark_results(rows, args.output)
    return 0


def run_benchmark_ras_batch(args: argparse.Namespace) -> int:
    args = resolve_run_ras_options(args)
    questions = load_benchmark_questions(args.dataset, limit=args.limit)
    if not questions:
        raise SystemExit(f"No benchmark questions found in dataset: {args.dataset}")
    print(f"loaded benchmark questions: {len(questions)}")
    rows = run_ras_benchmark(
        questions,
        model_service_url=args.model_service_url,
        organization_id=args.organization_id,
        embedding_model_id=args.embedding_model_id,
        embedding_use_case=args.embedding_use_case,
        embedding_dimensions=args.embedding_dimensions,
        llm_model_id=args.llm_model_id,
        llm_use_case=args.llm_use_case,
        elasticsearch_url=args.elasticsearch_url,
        elasticsearch_username=args.elasticsearch_username,
        elasticsearch_password=args.elasticsearch_password,
        elasticsearch_verify_certs=args.elasticsearch_verify_certs,
        index_name=args.index_name,
        top_k=args.top_k,
        num_candidates=args.num_candidates,
        max_rounds=args.max_rounds,
        max_follow_up_queries=args.max_follow_up_queries,
        analysis_max_tokens=args.analysis_max_tokens,
        answer_max_tokens=args.answer_max_tokens,
        temperature=args.llm_temperature,
        timeout=args.request_timeout,
        retries=args.request_retries,
        neo4j_uri=args.neo4j_uri,
        neo4j_username=args.neo4j_username,
        neo4j_password=args.neo4j_password,
        query_graph_namespace=args.query_graph_namespace,
        cleanup_query_graph=args.cleanup_query_graph,
    )
    write_benchmark_results(rows, args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project maintenance and benchmark CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_benchmark_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "benchmark" and args.benchmark_command == "index":
        return run_benchmark_index(args)
    if args.command == "benchmark" and args.benchmark_command == "graph-status":
        return run_graph_status(args)
    if args.command == "benchmark" and args.benchmark_command == "clean":
        return run_benchmark_clean(args)
    if args.command == "benchmark" and args.benchmark_command == "answer":
        return run_benchmark_answer(args)
    if args.command == "benchmark" and args.benchmark_command == "run-rag":
        return run_benchmark_rag_batch(args)
    if args.command == "benchmark" and args.benchmark_command == "run-ras":
        return run_benchmark_ras_batch(args)
    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
