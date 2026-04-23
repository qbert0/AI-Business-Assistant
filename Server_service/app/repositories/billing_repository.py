from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import messages
from app import models
from app.entities import database as db_entities
from app.entities.api import BillingSummaryEntity
from app.repositories.common import get_org_or_404, require_permission


def get_billing(org_id: str, acting_user_id: str, db: Session) -> BillingSummaryEntity:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, acting_user_id, "access_org_settings")
    records = (
        db.query(db_entities.BillingRecord)
        .filter(db_entities.BillingRecord.organization_id == org_id)
        .order_by(db_entities.BillingRecord.created_at.desc())
        .all()
    )
    return BillingSummaryEntity(
        organization_id=org_id,
        billing_plan=org.billing_plan,
        billing_status=org.billing_status,
        records=records,
    )


def create_billing_checkout(org_id: str, payload: models.BillingCheckoutCreate, db: Session) -> db_entities.BillingRecord:
    org = get_org_or_404(db, org_id)
    require_permission(db, org_id, payload.created_by_user_id, "access_org_settings")
    record = db_entities.BillingRecord(
        organization_id=org_id,
        created_by_user_id=payload.created_by_user_id,
        plan=payload.plan,
        status="pending",
        amount=str(payload.amount),
        currency=payload.currency,
        provider=payload.provider,
        provider_reference=payload.provider_reference,
    )
    org.billing_plan = payload.plan
    org.billing_status = "pending" if payload.plan != "free" else "active"
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_billing_record(
    record_id: str,
    payload: models.BillingStatusUpdate,
    acting_user_id: str,
    db: Session,
) -> db_entities.BillingRecord:
    record = db.get(db_entities.BillingRecord, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.BILLING_RECORD_NOT_FOUND)
    org = get_org_or_404(db, record.organization_id)
    require_permission(db, record.organization_id, acting_user_id, "access_org_settings")
    record.status = payload.status
    if payload.provider_reference is not None:
        record.provider_reference = payload.provider_reference
    if payload.status == "paid":
        org.billing_plan = record.plan
        org.billing_status = "active"
    elif payload.status in {"failed", "canceled"}:
        org.billing_status = payload.status
    db.commit()
    db.refresh(record)
    return record
