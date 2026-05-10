from app import models
from app.entities import database as db_entities
from app.repositories.common import parse_json_dict, parse_json_list


def to_user_model(user: db_entities.User) -> models.UserRead:
    return models.UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        public_profile=user.public_profile,
        avatar_url=user.avatar_url,
        default_organization_id=user.default_organization_id,
        locale=user.locale,
        timezone=user.timezone,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def to_organization_model(org: db_entities.Organization) -> models.OrganizationRead:
    return models.OrganizationRead(
        id=org.id,
        name=org.name,
        industry=org.industry,
        description=org.description,
        sensitive_restrictions=org.sensitive_restrictions,
        billing_plan=org.billing_plan,
        billing_status=org.billing_status,
        settings=parse_json_dict(org.settings_json),
        created_at=org.created_at,
    )


def to_member_model(member: db_entities.OrganizationMember) -> models.MemberRead:
    return models.MemberRead(
        id=member.id,
        user_id=member.user_id,
        organization_id=member.organization_id,
        role=member.role,
        permissions=parse_json_list(member.permissions),
        status=member.status,
        joined_at=member.joined_at,
        user=to_user_model(member.user),
    )


def to_billing_record_model(record: db_entities.BillingRecord) -> models.BillingRecordRead:
    return models.BillingRecordRead(
        id=record.id,
        organization_id=record.organization_id,
        created_by_user_id=record.created_by_user_id,
        plan=record.plan,
        status=record.status,
        amount=int(record.amount or 0),
        currency=record.currency,
        provider=record.provider,
        provider_reference=record.provider_reference,
        created_at=record.created_at,
    )


def parse_settings_json(org: db_entities.Organization) -> dict:
    return parse_json_dict(org.settings_json)
