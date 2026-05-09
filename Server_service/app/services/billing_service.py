from sqlalchemy.orm import Session

from app import models
from app.entities import database as db_entities
from app.entities.api import BillingSummaryEntity
from app.repositories import billing_repository


class BillingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_billing(self, org_id: str, acting_user_id: str) -> BillingSummaryEntity:
        return billing_repository.get_billing(org_id, acting_user_id, self.db)

    def create_billing_checkout(self, org_id: str, payload: models.BillingCheckoutCreate) -> db_entities.BillingRecord:
        return billing_repository.create_billing_checkout(org_id, payload, self.db)

    def update_billing_record(
        self,
        record_id: str,
        payload: models.BillingStatusUpdate,
        acting_user_id: str,
    ) -> db_entities.BillingRecord:
        return billing_repository.update_billing_record(record_id, payload, acting_user_id, self.db)
