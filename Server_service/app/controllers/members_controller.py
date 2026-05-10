from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dtos import common_dto, member_dto
from app.services import MembersService

router = APIRouter()


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
    member = MembersService(db).add_member(org_id, payload, acting_user_id)
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
    return member_dto.to_member_models(
        MembersService(db).list_members(org_id, acting_user_id=acting_user_id, search=search, skip=skip, limit=limit)
    )


@router.patch("/organizations/{org_id}/members/{member_id}", response_model=models.MemberRead, tags=["Members & RBAC"], summary="Cap nhat role/permission nhan vien")
def update_member(
    org_id: str,
    member_id: str,
    payload: models.MemberPatch,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> models.MemberRead:
    member = MembersService(db).update_member(org_id, member_id, payload, acting_user_id)
    return common_dto.to_member_model(member)


@router.delete("/organizations/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Members & RBAC"], summary="Xoa nhan vien khoi to chuc")
def delete_member(
    org_id: str,
    member_id: str,
    acting_user_id: str = Query(..., description="Can quyen access_org_settings."),
    db: Session = Depends(get_db),
) -> None:
    MembersService(db).delete_member(org_id, member_id, acting_user_id)


@router.post(
    "/organizations/{org_id}/membership/accept",
    response_model=models.MemberRead,
    tags=["Members & RBAC"],
    summary="Nhan vien chap nhan loi moi vao to chuc",
)
def accept_membership(
    org_id: str,
    acting_user_id: str = Query(..., description="User chap nhan loi moi cua chinh minh."),
    db: Session = Depends(get_db),
) -> models.MemberRead:
    member = MembersService(db).accept_membership(org_id, acting_user_id)
    return common_dto.to_member_model(member)


@router.post(
    "/organizations/{org_id}/membership/decline",
    response_model=models.MemberRead,
    tags=["Members & RBAC"],
    summary="Nhan vien tu choi loi moi vao to chuc",
)
def decline_membership(
    org_id: str,
    acting_user_id: str = Query(..., description="User tu choi loi moi cua chinh minh."),
    db: Session = Depends(get_db),
) -> models.MemberRead:
    member = MembersService(db).decline_membership(org_id, acting_user_id)
    return common_dto.to_member_model(member)


@router.delete("/organizations/{org_id}/membership", status_code=status.HTTP_204_NO_CONTENT, tags=["Members & RBAC"], summary="Roi khoi to chuc")
def leave_organization(
    org_id: str,
    acting_user_id: str = Query(..., description="User muon roi khoi to chuc."),
    db: Session = Depends(get_db),
) -> None:
    MembersService(db).leave_organization(org_id, acting_user_id)
