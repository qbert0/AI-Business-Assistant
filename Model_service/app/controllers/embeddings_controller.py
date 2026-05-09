from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_db, get_settings
from app.services.embedding_service import EmbeddingService


router = APIRouter(prefix="/embeddings", tags=["Embeddings"])


@router.post("", response_model=models.EmbeddingResultRead, summary="Tao embedding tu model upstream")
def create_embedding(payload: models.EmbeddingCreate, db: Session = Depends(get_db)) -> models.EmbeddingResultRead:
    return EmbeddingService.from_dependencies(db, get_settings()).create_embedding(payload)
