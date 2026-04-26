from app.core.serialization import parse_json_dict
from app.entities import database as entities
from app.models.feedback_model import FeedbackRead


def to_feedback_model(feedback: entities.FeedbackEvent) -> FeedbackRead:
    return FeedbackRead(
        id=feedback.id,
        request_id=feedback.request_id,
        conversation_id=feedback.conversation_id,
        organization_id=feedback.organization_id,
        user_id=feedback.user_id,
        model_id=feedback.model_id,
        rating=feedback.rating,
        comment=feedback.comment,
        metadata=parse_json_dict(feedback.metadata_json),
        created_at=feedback.created_at,
    )

