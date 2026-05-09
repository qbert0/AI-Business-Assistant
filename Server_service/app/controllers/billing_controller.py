from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.dtos import billing_dto, common_dto
from app.services import BillingService

router = APIRouter()


@router.get("/organizations/{org_id}/billing", response_model=models.BillingSummary, tags=["Billing"], summary="Lay thong tin thanh toan cua to chuc")
def get_billing(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.BillingSummary:
    billing = BillingService(db).get_billing(org_id, acting_user_id)
    return billing_dto.to_billing_summary_model(billing)


@router.post("/organizations/{org_id}/billing/checkout", response_model=models.BillingRecordRead, status_code=status.HTTP_201_CREATED, tags=["Billing"], summary="Tao checkout/thanh toan cho goi dich vu")
def create_billing_checkout(
    org_id: str,
    payload: models.BillingCheckoutCreate,
    db: Session = Depends(get_db),
) -> models.BillingRecordRead:
    record = BillingService(db).create_billing_checkout(org_id, payload)
    return common_dto.to_billing_record_model(record)


@router.patch("/billing/records/{record_id}", response_model=models.BillingRecordRead, tags=["Billing"], summary="Cap nhat trang thai thanh toan")
def update_billing_record(
    record_id: str,
    payload: models.BillingStatusUpdate,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings trong to chuc cua billing record."),
    db: Session = Depends(get_db),
) -> models.BillingRecordRead:
    record = BillingService(db).update_billing_record(record_id, payload, acting_user_id)
    return common_dto.to_billing_record_model(record)
