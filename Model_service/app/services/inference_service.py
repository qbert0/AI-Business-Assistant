from app.core.config import Settings
from app.models.feedback_model import FeedbackCreate, FeedbackRead
from app.models.inference_model import InferenceCreate, InferenceListItem, InferenceResult
from app.repositories.inference_repository import InferenceRepository


class InferenceService:
    def __init__(self, repository: InferenceRepository) -> None:
        self.repository = repository

    @classmethod
    def from_dependencies(cls, db, settings: Settings) -> "InferenceService":
        return cls(InferenceRepository(db, settings))

    def create_inference(self, payload: InferenceCreate) -> InferenceResult:
        return self.repository.create_inference(payload)

    def list_inferences(
        self,
        *,
        conversation_id: str | None = None,
        organization_id: str | None = None,
        user_id: str | None = None,
        limit: int = 20,
    ) -> list[InferenceListItem]:
        return self.repository.list_inferences(
            conversation_id=conversation_id,
            organization_id=organization_id,
            user_id=user_id,
            limit=limit,
        )

    def get_inference(self, request_id: str) -> InferenceListItem:
        return self.repository.get_inference(request_id)

    def create_feedback(self, payload: FeedbackCreate) -> FeedbackRead:
        return self.repository.create_feedback(payload)

    def list_feedback(
        self,
        *,
        organization_id: str | None = None,
        conversation_id: str | None = None,
        model_id: str | None = None,
        limit: int = 50,
    ) -> list[FeedbackRead]:
        return self.repository.list_feedback(
            organization_id=organization_id,
            conversation_id=conversation_id,
            model_id=model_id,
            limit=limit,
        )
