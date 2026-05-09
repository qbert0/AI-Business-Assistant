from sqlalchemy.orm import Session

from app.models.context_model import ContextBuildRequest, ContextBuildResponse, StoredContextDetail, StoredContextRead
from app.repositories.context_repository import ContextRepository


class ContextService:
    def __init__(self, repository: ContextRepository | None = None) -> None:
        self.repository = repository or ContextRepository()

    def build_context(self, payload: ContextBuildRequest) -> ContextBuildResponse:
        return self.repository.build_context(payload)

    def list_stored_contexts(
        self,
        db: Session,
        *,
        conversation_id: str | None = None,
        organization_id: str | None = None,
        user_id: str | None = None,
        limit: int = 20,
    ) -> list[StoredContextRead]:
        return self.repository.list_stored_contexts(
            db,
            conversation_id=conversation_id,
            organization_id=organization_id,
            user_id=user_id,
            limit=limit,
        )

    def get_stored_context(self, db: Session, request_id: str) -> StoredContextDetail:
        return self.repository.get_stored_context(db, request_id)
