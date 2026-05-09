from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import messages, models
from app.entities import database as db_entities
from app.entities.api import OrganizationDashboardEntity
from app.repositories import organizations_repository
from app.repositories.common import dump_schema, parse_json_list


class OrganizationsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_user_or_404(self, user_id: str) -> db_entities.User:
        user = self.db.get(db_entities.User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
        return user

    def _get_org_or_404(self, org_id: str) -> db_entities.Organization:
        org = organizations_repository.get_organization(org_id, self.db)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)
        return org

    def _require_permission(self, org_id: str, user_id: str, permission: str) -> db_entities.OrganizationMember:
        membership = organizations_repository.get_membership(org_id, user_id, self.db)
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
        permissions = parse_json_list(membership.permissions)
        if membership.role != "admin" and permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
        return membership

    def create_organization(self, payload: models.OrganizationCreate) -> db_entities.Organization:
        self._get_user_or_404(payload.owner_user_id)
        return organizations_repository.create_organization(
            name=payload.name,
            industry=payload.industry,
            description=payload.description,
            owner_user_id=payload.owner_user_id,
            db=self.db,
        )

    def list_organizations(
        self,
        *,
        search: str | None,
        user_id: str | None,
        skip: int,
        limit: int,
    ) -> list[db_entities.Organization]:
        return organizations_repository.list_organizations(search, user_id, skip, limit, self.db)

    def get_organization(self, org_id: str) -> db_entities.Organization:
        return self._get_org_or_404(org_id)

    def update_organization(
        self,
        org_id: str,
        payload: models.OrganizationUpdate,
        acting_user_id: str,
    ) -> db_entities.Organization:
        org = self._get_org_or_404(org_id)
        self._require_permission(org_id, acting_user_id, "access_org_settings")
        for field, value in dump_schema(payload, exclude_unset=True).items():
            setattr(org, field, value)
        organizations_repository.save_organization(self.db)
        return organizations_repository.refresh_organization(org, self.db)

    def build_dashboard(self, org_id: str, acting_user_id: str) -> OrganizationDashboardEntity:
        org = self._get_org_or_404(org_id)
        if not organizations_repository.get_membership(org_id, acting_user_id, self.db):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User khong thuoc to chuc nay.")
        return organizations_repository.build_dashboard(org, self.db)
