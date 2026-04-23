from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.dtos import common_dto, organization_dto
from app.entities import database as db_entities
from app.repositories import organizations_repository

router = APIRouter()


@router.post(
    "/organizations",
    response_model=models.OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Organizations"],
    summary="Tao to chuc moi va gan owner lam admin",
)
def create_organization(payload: models.OrganizationCreate, db: Session = Depends(get_db)) -> models.OrganizationRead:
    org = organizations_repository.create_organization(payload, db)
    return common_dto.to_organization_model(org)


@router.get("/organizations", response_model=list[models.OrganizationRead], tags=["Organizations"], summary="Lay danh sach to chuc")
def list_organizations(
    search: str | None = Query(None, description="Tim theo ten, nganh nghe hoac mo ta."),
    user_id: str | None = Query(None, description="Neu truyen, chi lay to chuc user dang tham gia."),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.OrganizationRead]:
    orgs = organizations_repository.list_organizations(search, user_id, skip, limit, db)
    return organization_dto.to_organization_models(orgs)


@router.get("/organizations/{org_id}", response_model=models.OrganizationRead, tags=["Organizations"], summary="Lay chi tiet to chuc")
def get_organization(org_id: str, db: Session = Depends(get_db)) -> models.OrganizationRead:
    org = organizations_repository.get_organization(org_id, db)
    return common_dto.to_organization_model(org)


@router.patch("/organizations/{org_id}", response_model=models.OrganizationRead, tags=["Organizations"], summary="Cap nhat thong tin to chuc")
def update_organization(
    org_id: str,
    payload: models.OrganizationUpdate,
    acting_user_id: str = Query(..., description="User thuc hien thao tac, can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.OrganizationRead:
    org = organizations_repository.update_organization(org_id, payload, acting_user_id, db)
    return common_dto.to_organization_model(org)


@router.get("/organizations/{org_id}/dashboard", response_model=models.OrganizationDashboard, tags=["Organizations"], summary="Tong quan to chuc")
def organization_dashboard(
    org_id: str,
    acting_user_id: str = Query(..., description="User dang xem dashboard, phai thuoc to chuc."),
    db: Session = Depends(get_db),
) -> models.OrganizationDashboard:
    dashboard = organizations_repository.organization_dashboard(org_id, acting_user_id, db)
    return organization_dto.to_organization_dashboard_model(dashboard)
