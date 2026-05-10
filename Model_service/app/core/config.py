from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - fallback for environments still on Pydantic v1
    from pydantic import BaseSettings
    SettingsConfigDict = None


class Settings(BaseSettings):
    app_name: str = "AI Business Assistant Model Service"
    app_version: str = "0.1.0"
    database_url: str = "mysql+pymysql://model_service:model_service123@localhost:3307/model_service"
    model_service_secret_key: str = "change-this-model-service-secret"
    model_service_cors_origins: str = "*"
    default_inference_timeout_seconds: int = 360
    default_provider_timeout_seconds: int = 360
    database_pool_size: int = 20
    database_max_overflow: int = 40
    database_pool_timeout: int = 60
    database_pool_recycle: int = 1800

    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(case_sensitive=False)
    else:  # pragma: no cover - fallback for environments still on Pydantic v1
        class Config:
            case_sensitive = False

    @property
    def cors_origins(self) -> list[str]:
        raw = self.model_service_cors_origins.strip()
        if not raw or raw == "*":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
