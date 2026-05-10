import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import messages, models
from app.entities import database as db_entities
from app.repositories import members_repository
from app.repositories.common import parse_json_list
from app.repositories.notifications_repository import create_notification
from app.services.email_service import send_email
from app.services.security import permissions_for_role


class MembersService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_org_or_404(self, org_id: str) -> db_entities.Organization:
        org = self.db.get(db_entities.Organization, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.ORGANIZATION_NOT_FOUND)
        return org

    def _get_user_or_404(self, user_id: str) -> db_entities.User:
        user = self.db.get(db_entities.User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
        return user

    def _require_permission(self, org_id: str, user_id: str, permission: str) -> db_entities.OrganizationMember:
        membership = members_repository.get_membership(org_id, user_id, self.db)
        if not membership or membership.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_NOT_IN_ORGANIZATION)
        permissions = parse_json_list(membership.permissions)
        if membership.role != "admin" and permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Thieu quyen `{permission}`.")
        return membership

    def add_member(self, org_id: str, payload: models.MemberCreate, acting_user_id: str) -> db_entities.OrganizationMember:
        org = self._get_org_or_404(org_id)
        user = self._get_user_or_404(payload.user_id)
        self._require_permission(org_id, acting_user_id, "access_org_settings")
        if members_repository.get_membership(org_id, payload.user_id, self.db):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.MEMBER_ALREADY_EXISTS)
        member = members_repository.create_member(
            org_id=org_id,
            user_id=payload.user_id,
            role=payload.role,
            permissions=permissions_for_role(payload.role, payload.permissions),
            status_value=payload.status,
            db=self.db,
        )
        create_notification(
            models.NotificationCreate(
                user_id=user.id,
                organization_id=org.id,
                notification_type="organization",
                title=f"Ban co loi moi tham gia {org.name}",
                content=f"Vai tro duoc gan: {payload.role}. Trang thai hien tai: {payload.status}.",
                action_url="/notifications",
            ),
            self.db,
        )
        send_email(
            to_email=user.email,
            subject=f"Loi moi tham gia to chuc {org.name}",
            body=(
                f"Xin chao {user.full_name},\n\n"
                f"Ban vua duoc moi vao to chuc {org.name} voi vai tro {payload.role}.\n"
                "Dang nhap vao he thong de chap nhan loi moi va bat dau su dung workspace.\n"
            ),
        )
        return member

    def list_members(
        self,
        org_id: str,
        *,
        acting_user_id: str,
        search: str | None,
        skip: int,
        limit: int,
    ) -> list[db_entities.OrganizationMember]:
        self._require_permission(org_id, acting_user_id, "view_employees")
        return members_repository.list_members(org_id, search, skip, limit, self.db)

    def update_member(
        self,
        org_id: str,
        member_id: str,
        payload: models.MemberPatch,
        acting_user_id: str,
    ) -> db_entities.OrganizationMember:
        self._require_permission(org_id, acting_user_id, "access_org_settings")
        member = members_repository.get_member(member_id, org_id, self.db)
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
        members_repository.save_member(self.db)
        return members_repository.refresh_member(member, self.db)

    def delete_member(self, org_id: str, member_id: str, acting_user_id: str) -> None:
        self._require_permission(org_id, acting_user_id, "access_org_settings")
        member = members_repository.get_member(member_id, org_id, self.db)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.MEMBER_NOT_FOUND)
        members_repository.delete_member(member, self.db)

    def accept_membership(self, org_id: str, acting_user_id: str) -> db_entities.OrganizationMember:
        self._get_org_or_404(org_id)
        member = members_repository.get_membership(org_id, acting_user_id, self.db)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_IN_ORGANIZATION)
        if member.status == "disabled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.USER_DISABLED)
        member.status = "active"
        members_repository.save_member(self.db)
        return members_repository.refresh_member(member, self.db)

    def decline_membership(self, org_id: str, acting_user_id: str) -> db_entities.OrganizationMember:
        self._get_org_or_404(org_id)
        member = members_repository.get_membership(org_id, acting_user_id, self.db)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_IN_ORGANIZATION)
        if member.status == "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thanh vien da kich hoat.")
        if member.status == "disabled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.USER_DISABLED)
        member.status = "declined"
        members_repository.save_member(self.db)
        return members_repository.refresh_member(member, self.db)

    def leave_organization(self, org_id: str, acting_user_id: str) -> None:
        member = members_repository.get_membership(org_id, acting_user_id, self.db)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_IN_ORGANIZATION)
        if member.role == "admin" and members_repository.count_active_admins(org_id, self.db) <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.LAST_ADMIN_CANNOT_LEAVE)
        members_repository.delete_member(member, self.db)
