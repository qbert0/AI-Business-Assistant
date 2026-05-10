import os


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "business-documents")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
STORAGE_PUBLIC_ENDPOINT = os.getenv("STORAGE_PUBLIC_ENDPOINT", "").rstrip("/")

SEARCH_SERVICE_URL = os.getenv("SEARCH_SERVICE_URL", "http://search-service:8000").rstrip("/")
SEARCH_SERVICE_TIMEOUT = int(os.getenv("SEARCH_SERVICE_TIMEOUT", "10"))
MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://model_service:8888").rstrip("/")
MODEL_SERVICE_TIMEOUT = int(os.getenv("MODEL_SERVICE_TIMEOUT", "90"))
