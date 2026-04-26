from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import messages, models
from app.database import get_db
from app.dtos import common_dto, organization_dto
from app.entities import database as db_entities
from app.repositories import organizations_repository
from app.repositories.common import dump_schema, parse_json_list

router = APIRouter()


def _get_user(user_id: str, db: Session):
    user = db.get(db_entities.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
    return user


def _get_org_or_404(org_id: str, db: Session):
    org = organizations_repository.get_organization(org_id, db)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)
    return org


def _require_permission(org_id: str, user_id: str, permission: str, db: Session):
    membership = organizations_repository.get_membership(org_id, user_id, db)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
    permissions = parse_json_list(membership.permissions)
    if membership.role != "admin" and permission not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
    return membership


@router.post(
    "/organizations",
    response_model=models.OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Organizations"],
    summary="Tao to chuc moi va gan owner lam admin",
)
def create_organization(payload: models.OrganizationCreate, db: Session = Depends(get_db)) -> models.OrganizationRead:
    _get_user(payload.owner_user_id, db)
    org = organizations_repository.create_organization(
        name=payload.name,
        industry=payload.industry,
        description=payload.description,
        owner_user_id=payload.owner_user_id,
        db=db,
    )
    return common_dto.to_organization_model(org)


@router.get("/organizations", response_model=list[models.OrganizationRead], tags=["Organizations"], summary="Lay danh sach to chuc")
def list_organizations(
    search: str | None = Query(None, description="Tim theo ten, nganh nghe hoac mo ta."),
    user_id: str | None = Query(None, description="Neu truyen, chi lay to chuc user dang tham gia."),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.OrganizationRead]:
    return organization_dto.to_organization_models(organizations_repository.list_organizations(search, user_id, skip, limit, db))


@router.get("/organizations/{org_id}", response_model=models.OrganizationRead, tags=["Organizations"], summary="Lay chi tiet to chuc")
def get_organization(org_id: str, db: Session = Depends(get_db)) -> models.OrganizationRead:
    return common_dto.to_organization_model(_get_org_or_404(org_id, db))


@router.patch("/organizations/{org_id}", response_model=models.OrganizationRead, tags=["Organizations"], summary="Cap nhat thong tin to chuc")
def update_organization(
    org_id: str,
    payload: models.OrganizationUpdate,
    acting_user_id: str = Query(..., description="User thuc hien thao tac, can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.OrganizationRead:
    org = _get_org_or_404(org_id, db)
    _require_permission(org_id, acting_user_id, "access_org_settings", db)
    for field, value in dump_schema(payload, exclude_unset=True).items():
        setattr(org, field, value)
    organizations_repository.save_organization(db)
    organizations_repository.refresh_organization(org, db)
    return common_dto.to_organization_model(org)


@router.get("/organizations/{org_id}/dashboard", response_model=models.OrganizationDashboard, tags=["Organizations"], summary="Tong quan to chuc")
def organization_dashboard(
    org_id: str,
    acting_user_id: str = Query(..., description="User dang xem dashboard, phai thuoc to chuc."),
    db: Session = Depends(get_db),
) -> models.OrganizationDashboard:
    org = _get_org_or_404(org_id, db)
    if not organizations_repository.get_membership(org_id, acting_user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User khong thuoc to chuc nay.")
    dashboard = organizations_repository.build_dashboard(org, db)
    return organization_dto.to_organization_dashboard_model(dashboard)
