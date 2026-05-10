import os
from pathlib import Path

import yaml


def get_root_path():
    return Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


ROOT_PATH = get_root_path()
CONFIG_PATH = ROOT_PATH / "configs"
CONFIG_FILE_PATH = CONFIG_PATH / "config.yaml"

if CONFIG_FILE_PATH.exists():
    with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader) or {}
else:
    config = {}

WORKER_CONFIG = config.get("worker", {})
REDIS_CONFIG = config.get("redis", {})
RAG_CONFIG = config.get("rag_service", {})
SERVER_CONFIG = config.get("server_service", {})

LLM_STREAM_LOG = config.get("llm_config", {}).get("stream_log", False)

WORKER_CONCURRENT = int(WORKER_CONFIG.get("concurrent", 33))
WORKER_QUEUE_NAME = WORKER_CONFIG.get("queue_name", "file-preprocess")
WORKER_GROUP_NAME = WORKER_CONFIG.get("group_name", WORKER_QUEUE_NAME)
WORKER_CONSUMER_NAME = WORKER_CONFIG.get("consumer_name")
WORKER_BATCH_SIZE = int(WORKER_CONFIG.get("batch_size", 20))
WORKER_BLOCK_MS = int(WORKER_CONFIG.get("block_ms", 5000))
WORKER_MAX_PENDING_RETRY = int(WORKER_CONFIG.get("max_pending_retry", 100))

REDIS_HOST = REDIS_CONFIG.get("host", "redis")
REDIS_PORT = int(REDIS_CONFIG.get("port", 6379))
REDIS_DB = int(REDIS_CONFIG.get("db", 0))
REDIS_PASSWORD = REDIS_CONFIG.get("password")

RAG_SERVICE_URL = RAG_CONFIG.get("url", "http://rag-service:8000")
SERVER_SERVICE_URL = SERVER_CONFIG.get("url", "http://server_service:8000")
