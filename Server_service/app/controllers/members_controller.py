import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import messages, models
from app.database import get_db
from app.dtos import common_dto, member_dto
from app.entities import database as db_entities
from app.repositories import members_repository
from app.repositories.common import parse_json_list
from app.services.security import permissions_for_role

router = APIRouter()


def _get_org(org_id: str, db: Session) -> db_entities.Organization:
    org = db.get(db_entities.Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)
    return org


def _get_user(user_id: str, db: Session) -> db_entities.User:
    user = db.get(db_entities.User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
    return user


def _require_permission(org_id: str, user_id: str, permission: str, db: Session) -> db_entities.OrganizationMember:
    membership = members_repository.get_membership(org_id, user_id, db)
    if not membership or membership.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
    permissions = parse_json_list(membership.permissions)
    if membership.role != "admin" and permission not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
    return membership


@router.post(
    "/organizations/{org_id}/members",
    response_model=models.MemberRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Members & RBAC"],
    summary="Them nhan vien vao to chuc",
)
def add_member(
    org_id: str,
    payload: models.MemberCreate,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.MemberRead:
    _get_org(org_id, db)
    _get_user(payload.user_id, db)
    _require_permission(org_id, acting_user_id, "access_org_settings", db)
    if members_repository.get_membership(org_id, payload.user_id, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.MEMBER_ALREADY_EXISTS)
    member = members_repository.create_member(
        org_id=org_id,
        user_id=payload.user_id,
        role=payload.role,
        permissions=permissions_for_role(payload.role, payload.permissions),
        status_value=payload.status,
        db=db,
    )
    return common_dto.to_member_model(member)


@router.get("/organizations/{org_id}/members", response_model=list[models.MemberRead], tags=["Members & RBAC"], summary="Lay danh sach nhan vien")
def list_members(
    org_id: str,
    acting_user_id: str = Query(..., description="Can quyen view_employees."),
    search: str | None = Query(None, description="Tim theo ten hoac email."),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.MemberRead]:
    _require_permission(org_id, acting_user_id, "view_employees", db)
    return member_dto.to_member_models(members_repository.list_members(org_id, search, skip, limit, db))


@router.patch("/organizations/{org_id}/members/{member_id}", response_model=models.MemberRead, tags=["Members & RBAC"], summary="Cap nhat role/permission nhan vien")
def update_member(
    org_id: str,
    member_id: str,
    payload: models.MemberPatch,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.MemberRead:
    _require_permission(org_id, acting_user_id, "access_org_settings", db)
    member = members_repository.get_member(member_id, org_id, db)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.MEMBER_NOT_FOUND)
    if payload.role is not None:
        member.role = payload.role
        if payload.permissions is None:
            member.permissions = json.dumps(permissions_for_role(payload.role))
    if payload.permissions is not None:
        member.permissions = json.dumps(permissions_for_role(payload.role or member.role, payload.permissions))
    if payload.status is not None:
        member.status = payload.status
    members_repository.save_member(db)
    members_repository.refresh_member(member, db)
    return common_dto.to_member_model(member)


@router.delete("/organizations/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Members & RBAC"], summary="Xoa nhan vien khoi to chuc")
def delete_member(
    org_id: str,
    member_id: str,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> None:
    _require_permission(org_id, acting_user_id, "access_org_settings", db)
    member = members_repository.get_member(member_id, org_id, db)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.MEMBER_NOT_FOUND)
    members_repository.delete_member(member, db)


@router.delete("/organizations/{org_id}/membership", status_code=status.HTTP_204_NO_CONTENT, tags=["Members & RBAC"], summary="Roi khoi to chuc")
def leave_organization(
    org_id: str,
    acting_user_id: str = Query(..., description="User muon roi khoi to chuc."),
    db: Session = Depends(get_db),
) -> None:
    member = members_repository.get_membership(org_id, acting_user_id, db)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_IN_ORGANIZATION)
    if member.role == "admin" and members_repository.count_active_admins(org_id, db) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.LAST_ADMIN_CANNOT_LEAVE)
    members_repository.delete_member(member, db)
