from dataclasses import dataclass, field

from app.entities import database as db_entities


@dataclass(slots=True)
class TokenEntity:
    access_token: str
    expires_in_seconds: int
    user: db_entities.User
    token_type: str = "bearer"


@dataclass(slots=True)
class OrganizationDashboardEntity:
    organization: db_entities.Organization
    employee_count: int
    document_count: int
    indexed_document_count: int
    chat_session_count: int
    suggested_questions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AnalyticsEntity:
    organization_id: str
    employee_count: int
    document_count: int
    indexed_document_count: int
    chat_session_count: int
    question_count: int
    popular_questions: list[str] = field(default_factory=list)
    sensitive_restrictions: str | None = None


@dataclass(slots=True)
class OrganizationSettingsEntity:
    organization: db_entities.Organization
    settings: dict


@dataclass(slots=True)
class BillingSummaryEntity:
    organization_id: str
    billing_plan: str
    billing_status: str
    records: list[db_entities.BillingRecord] = field(default_factory=list)
