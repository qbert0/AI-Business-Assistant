from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dtos import common_dto, organization_dto
from app.services import OrganizationsService

router = APIRouter()


@router.post(
    "/organizations",
    response_model=models.OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Organizations"],
    summary="Tao to chuc moi va gan owner lam admin",
)
def create_organization(payload: models.OrganizationCreate, db: Session = Depends(get_db)) -> models.OrganizationRead:
    org = OrganizationsService(db).create_organization(payload)
    return common_dto.to_organization_model(org)


@router.get("/organizations", response_model=list[models.OrganizationRead], tags=["Organizations"], summary="Lay danh sach to chuc")
def list_organizations(
    search: str | None = Query(None, description="Tim theo ten, nganh nghe hoac mo ta."),
    user_id: str | None = Query(None, description="Neu truyen, chi lay to chuc user dang tham gia."),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.OrganizationRead]:
    return organization_dto.to_organization_models(
        OrganizationsService(db).list_organizations(search=search, user_id=user_id, skip=skip, limit=limit)
    )


@router.get("/organizations/{org_id}", response_model=models.OrganizationRead, tags=["Organizations"], summary="Lay chi tiet to chuc")
def get_organization(org_id: str, db: Session = Depends(get_db)) -> models.OrganizationRead:
    return common_dto.to_organization_model(OrganizationsService(db).get_organization(org_id))


@router.patch("/organizations/{org_id}", response_model=models.OrganizationRead, tags=["Organizations"], summary="Cap nhat thong tin to chuc")
def update_organization(
    org_id: str,
    payload: models.OrganizationUpdate,
    acting_user_id: str = Query(..., description="User thuc hien thao tac, can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.OrganizationRead:
    org = OrganizationsService(db).update_organization(org_id, payload, acting_user_id)
    return common_dto.to_organization_model(org)


@router.get("/organizations/{org_id}/dashboard", response_model=models.OrganizationDashboard, tags=["Organizations"], summary="Tong quan to chuc")
def organization_dashboard(
    org_id: str,
    acting_user_id: str = Query(..., description="User dang xem dashboard, phai thuoc to chuc."),
    db: Session = Depends(get_db),
) -> models.OrganizationDashboard:
    dashboard = OrganizationsService(db).build_dashboard(org_id, acting_user_id)
    return organization_dto.to_organization_dashboard_model(dashboard)
