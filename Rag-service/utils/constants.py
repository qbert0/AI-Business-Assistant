import os
from pathlib import Path

import yaml


def get_root_path():
    return Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


ROOT_PATH = get_root_path()
CONFIG_PATH = ROOT_PATH / "configs"
CONFIG_FILE_PATH = CONFIG_PATH / "config.yaml"

MARKDOWN_TITLE_PREFIX = "## "

if CONFIG_FILE_PATH.exists():
    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader) or {}
else:
    config = {}

APP_CONFIG = config.get("app", {})
NEO4J_CONFIG = config.get("neo4j", {})
MODEL_SERVICE_CONFIG = config.get("model_service", {})
REDIS_CONFIG = config.get("redis", {})
INGEST_QUEUE_CONFIG = config.get("ingest_queue", {})
SERVER_SERVICE_CONFIG = config.get("server_service", {})

LLM_STREAM_LOG = config.get("llm_config", {}).get("stream_log", False)
LLM_RESPONSE_LOG = config.get("llm_config", {}).get("response_log", True)
LLM_RESPONSE_LOG_MAX_CHARS = int(config.get("llm_config", {}).get("response_log_max_chars", 12000))
APP_HOST = APP_CONFIG.get("host", "0.0.0.0")
APP_PORT = int(APP_CONFIG.get("port", 8000))

NEO4J_URI = NEO4J_CONFIG.get("uri", "bolt://neo4j:7687")
NEO4J_USERNAME = NEO4J_CONFIG.get("username", "neo4j")
NEO4J_PASSWORD = NEO4J_CONFIG.get("password", "pleaseletmein")

MODEL_SERVICE_URL = MODEL_SERVICE_CONFIG.get("url", "http://model-service:8888")
MODEL_SERVICE_ORGANIZATION_ID = MODEL_SERVICE_CONFIG.get("organization_id", "rag-service")
MODEL_SERVICE_LLM_MODEL_ID = MODEL_SERVICE_CONFIG.get("llm_model_id")
MODEL_SERVICE_EMBEDDING_MODEL_ID = MODEL_SERVICE_CONFIG.get("embedding_model_id")
MODEL_SERVICE_RERANKER_MODEL_ID = MODEL_SERVICE_CONFIG.get("reranker_model_id")
MODEL_SERVICE_INFERENCE_USE_CASE = MODEL_SERVICE_CONFIG.get(
    "inference_use_case",
    "graphiti_extraction",
)
MODEL_SERVICE_EMBEDDING_USE_CASE = MODEL_SERVICE_CONFIG.get(
    "embedding_use_case",
    "embeddings",
)
MODEL_SERVICE_TIMEOUT_SECONDS = float(MODEL_SERVICE_CONFIG.get("timeout_seconds", 180))
MODEL_SERVICE_MAX_RETRIES = int(MODEL_SERVICE_CONFIG.get("max_retries", 1))
MODEL_SERVICE_RETRY_BACKOFF_SECONDS = float(MODEL_SERVICE_CONFIG.get("retry_backoff_seconds", 2.0))

REDIS_HOST = REDIS_CONFIG.get("host", "redis")
REDIS_PORT = int(REDIS_CONFIG.get("port", 6379))
REDIS_DB = int(REDIS_CONFIG.get("db", 0))
REDIS_PASSWORD = REDIS_CONFIG.get("password")
SERVER_SERVICE_URL = SERVER_SERVICE_CONFIG.get("url", "http://server_service:8000")

INGEST_QUEUE_NAME = INGEST_QUEUE_CONFIG.get("queue_name", "rag-ingest")
INGEST_GROUP_NAME = INGEST_QUEUE_CONFIG.get("group_name", INGEST_QUEUE_NAME)
INGEST_CONSUMER_NAME = INGEST_QUEUE_CONFIG.get("consumer_name")
INGEST_CONCURRENT = int(INGEST_QUEUE_CONFIG.get("concurrent", 1))
INGEST_BATCH_SIZE = int(INGEST_QUEUE_CONFIG.get("batch_size", 1))
INGEST_BLOCK_MS = int(INGEST_QUEUE_CONFIG.get("block_ms", 5000))

HEALTH_ROUTE_PREFIX = "/health"
COMPAT_ROUTE_PREFIX = "/compat"
INGEST_ROUTE_PREFIX = "/ingest"
SEARCH_ROUTE_PREFIX = "/search"
GRAPH_ROUTE_PREFIX = "/graph"
