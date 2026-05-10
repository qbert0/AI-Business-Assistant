from app import models
from app.entities.api import AnalyticsEntity


def to_analytics_model(entity: AnalyticsEntity) -> models.AnalyticsRead:
    return models.AnalyticsRead(
        organization_id=entity.organization_id,
        employee_count=entity.employee_count,
        document_count=entity.document_count,
        indexed_document_count=entity.indexed_document_count,
        chat_session_count=entity.chat_session_count,
        question_count=entity.question_count,
        popular_questions=entity.popular_questions,
        popular_question_stats=entity.popular_question_stats,
        feedback_summary=entity.feedback_summary,
        feedback_items=entity.feedback_items,
        sensitive_restrictions=entity.sensitive_restrictions,
    )
