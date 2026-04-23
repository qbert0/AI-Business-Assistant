from app import models
from app.dtos.common_dto import to_organization_model
from app.entities.api import OrganizationDashboardEntity
from app.entities import database as db_entities


def to_organization_models(orgs: list[db_entities.Organization]) -> list[models.OrganizationRead]:
    return [to_organization_model(org) for org in orgs]


def to_organization_dashboard_model(entity: OrganizationDashboardEntity) -> models.OrganizationDashboard:
    return models.OrganizationDashboard(
        organization=to_organization_model(entity.organization),
        employee_count=entity.employee_count,
        document_count=entity.document_count,
        indexed_document_count=entity.indexed_document_count,
        chat_session_count=entity.chat_session_count,
        suggested_questions=entity.suggested_questions,
    )
