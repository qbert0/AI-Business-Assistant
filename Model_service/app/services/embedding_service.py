from app.core.config import Settings
from app.models.embedding_model import EmbeddingCreate, EmbeddingResultRead
from app.repositories.embedding_repository import EmbeddingRepository


class EmbeddingService:
    def __init__(self, repository: EmbeddingRepository) -> None:
        self.repository = repository

    @classmethod
    def from_dependencies(cls, db, settings: Settings) -> "EmbeddingService":
        return cls(EmbeddingRepository(db, settings))

    def create_embedding(self, payload: EmbeddingCreate) -> EmbeddingResultRead:
        return self.repository.create_embedding(payload)
