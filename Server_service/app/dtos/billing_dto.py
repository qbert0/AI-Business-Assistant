from app import models
from app.dtos.common_dto import to_billing_record_model
from app.entities.api import BillingSummaryEntity


def to_billing_summary_model(entity: BillingSummaryEntity) -> models.BillingSummary:
    return models.BillingSummary(
        organization_id=entity.organization_id,
        billing_plan=entity.billing_plan,
        billing_status=entity.billing_status,
        records=[to_billing_record_model(record) for record in entity.records],
    )
