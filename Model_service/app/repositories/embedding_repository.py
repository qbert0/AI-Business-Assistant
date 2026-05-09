from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import decrypt_secret
from app.db import models as db_models
from app.infrastructure.embedding.base import EmbeddingResult, ProviderRequestError
from app.infrastructure.embedding.factory import build_embedding_client
from app.models.embedding_model import EmbeddingCreate, EmbeddingResultRead, EmbeddingUsageRead, EmbeddingVectorRead
from app.repositories.registry_repository import RegistryRepository


class EmbeddingRepository:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.registry_repository = RegistryRepository(db, settings)

    def _run_embedding(
        self,
        model: db_models.RegisteredModel,
        payload: EmbeddingCreate,
    ) -> EmbeddingResult:
        client = build_embedding_client(
            model,
            decrypt_secret(model.api_key_encrypted, self.settings),
            self.settings.default_provider_timeout_seconds,
        )
        return client.embed(
            payload.input,
            dimensions=payload.dimensions,
            metadata=payload.metadata,
        )

    def create_embedding(self, payload: EmbeddingCreate) -> EmbeddingResultRead:
        model = self.registry_repository.resolve_runtime_model(
            model_id=payload.model_id,
            model_name=payload.model,
            kind="embedding",
        )
        try:
            result = self._run_embedding(model, payload)
        except (ProviderRequestError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Khong the goi embedding upstream: {exc}",
            ) from exc

        dimensions = len(result.vectors[0].embedding) if result.vectors else 0
        return EmbeddingResultRead(
            model_id=model.id,
            model_name=model.model_name,
            provider_type=model.provider.provider_type,
            dimensions=dimensions,
            data=[
                EmbeddingVectorRead(index=item.index, embedding=item.embedding)
                for item in result.vectors
            ],
            usage=EmbeddingUsageRead(
                prompt_tokens=result.prompt_tokens,
                total_tokens=result.total_tokens,
            ),
        )
