from datetime import datetime

from app.core.serialization import parse_json_dict, parse_json_list
from app.entities import database as entities
from app.models import registry_model, provider_model


def to_provider_model(provider: entities.Provider) -> provider_model.ProviderRead:
    return provider_model.ProviderRead(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        description=provider.description,
        metadata=parse_json_dict(provider.metadata_json),
        is_active=provider.is_active,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


def to_model_model(model: entities.RegisteredModel) -> registry_model.ModelRead:
    return registry_model.ModelRead(
        id=model.id,
        provider_id=model.provider_id,
        display_name=model.display_name,
        model_name=model.model_name,
        base_url=model.base_url,
        api_key_masked=model.api_key_masked,
        capabilities=parse_json_list(model.capabilities_json),
        parameters=parse_json_dict(model.parameters_json),
        priority=model.priority,
        is_default=model.is_default,
        is_active=model.is_active,
        health_status=model.health_status,
        last_checked_at=model.last_checked_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_policy_model(policy: entities.ModelPolicy) -> registry_model.PolicyRead:
    return registry_model.PolicyRead(
        id=policy.id,
        organization_id=policy.organization_id,
        use_case=policy.use_case,
        default_model_id=policy.default_model_id,
        fallback_model_id=policy.fallback_model_id,
        temperature=policy.temperature,
        max_tokens=policy.max_tokens,
        system_prompt=policy.system_prompt,
        metadata=parse_json_dict(policy.metadata_json),
        is_active=policy.is_active,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


def to_model_health_check_model(
    model_id: str,
    status: str,
    detail: str,
    checked_at: datetime,
) -> registry_model.ModelHealthCheckRead:
    return registry_model.ModelHealthCheckRead(
        model_id=model_id,
        status=status,
        detail=detail,
        checked_at=checked_at,
    )

