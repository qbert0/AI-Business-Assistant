from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.core.security import decrypt_secret, encrypt_secret, mask_secret
from app.core.serialization import dump_json, parse_json_dict, parse_json_list
from app.db import models as db_models
from app.infrastructure.llm.base import ProviderRequestError
from app.infrastructure.llm.factory import build_llm_client
from app.schemas.model import (
    ModelCreate,
    ModelHealthCheckRead,
    ModelRead,
    ModelUpdate,
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
)
from app.schemas.provider import ProviderCreate, ProviderRead, ProviderUpdate


class RegistryService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def _serialize_provider(self, provider: db_models.Provider) -> ProviderRead:
        return ProviderRead(
            id=provider.id,
            name=provider.name,
            provider_type=provider.provider_type,
            description=provider.description,
            metadata=parse_json_dict(provider.metadata_json),
            is_active=provider.is_active,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )

    def _serialize_model(self, model: db_models.RegisteredModel) -> ModelRead:
        return ModelRead(
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

    def _serialize_policy(self, policy: db_models.ModelPolicy) -> PolicyRead:
        return PolicyRead(
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

    def list_providers(self, name: str | None = None) -> list[ProviderRead]:
        query = self.db.query(db_models.Provider)
        if name:
            pattern = f"%{name.strip()}%"
            query = query.filter(db_models.Provider.name.ilike(pattern))
        providers = query.order_by(db_models.Provider.name.asc()).all()
        return [self._serialize_provider(provider) for provider in providers]

    def get_provider(self, provider_id: str) -> ProviderRead:
        provider = self.db.get(db_models.Provider, provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider khong ton tai.")
        return self._serialize_provider(provider)

    def create_provider(self, payload: ProviderCreate) -> ProviderRead:
        existing = self.db.query(db_models.Provider).filter(db_models.Provider.name == payload.name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Provider da ton tai.")
        provider = db_models.Provider(
            name=payload.name,
            provider_type=payload.provider_type,
            description=payload.description,
            metadata_json=dump_json(payload.metadata),
            is_active=payload.is_active,
        )
        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)
        return self._serialize_provider(provider)

    def update_provider(self, provider_id: str, payload: ProviderUpdate) -> ProviderRead:
        provider = self.db.get(db_models.Provider, provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider khong ton tai.")
        updates = payload.dict(exclude_unset=True)
        for field, value in updates.items():
            if field == "metadata":
                provider.metadata_json = dump_json(value)
            else:
                setattr(provider, field, value)
        self.db.commit()
        self.db.refresh(provider)
        return self._serialize_provider(provider)

    def delete_provider(self, provider_id: str) -> None:
        provider = self.db.get(db_models.Provider, provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider khong ton tai.")
        self.db.delete(provider)
        self.db.commit()

    def _get_provider_entity(self, provider_id: str) -> db_models.Provider:
        provider = self.db.get(db_models.Provider, provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider khong ton tai.")
        return provider

    def _get_model_entity(self, model_id: str) -> db_models.RegisteredModel:
        model = (
            self.db.query(db_models.RegisteredModel)
            .options(joinedload(db_models.RegisteredModel.provider))
            .filter(db_models.RegisteredModel.id == model_id)
            .first()
        )
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model khong ton tai.")
        return model

    def _ensure_single_default(self, model_id: str | None = None) -> None:
        query = self.db.query(db_models.RegisteredModel)
        if model_id:
            query = query.filter(db_models.RegisteredModel.id != model_id)
        query.update({db_models.RegisteredModel.is_default: False}, synchronize_session=False)

    def list_models(
        self,
        provider_id: str | None = None,
        is_active: bool | None = None,
        provider_name: str | None = None,
        model_name: str | None = None,
    ) -> list[ModelRead]:
        query = self.db.query(db_models.RegisteredModel)
        if provider_name:
            query = query.join(db_models.RegisteredModel.provider)
        query = query.order_by(
            db_models.RegisteredModel.is_default.desc(),
            db_models.RegisteredModel.priority.asc(),
            db_models.RegisteredModel.display_name.asc(),
        )
        if provider_id:
            query = query.filter(db_models.RegisteredModel.provider_id == provider_id)
        if is_active is not None:
            query = query.filter(db_models.RegisteredModel.is_active == is_active)
        if provider_name:
            provider_pattern = f"%{provider_name.strip()}%"
            query = query.filter(db_models.Provider.name.ilike(provider_pattern))
        if model_name:
            model_pattern = f"%{model_name.strip()}%"
            query = query.filter(
                or_(
                    db_models.RegisteredModel.model_name.ilike(model_pattern),
                    db_models.RegisteredModel.display_name.ilike(model_pattern),
                )
            )
        return [self._serialize_model(item) for item in query.all()]

    def get_model(self, model_id: str) -> ModelRead:
        return self._serialize_model(self._get_model_entity(model_id))

    def create_model(self, payload: ModelCreate) -> ModelRead:
        self._get_provider_entity(payload.provider_id)
        if payload.is_default:
            self._ensure_single_default()
        model = db_models.RegisteredModel(
            provider_id=payload.provider_id,
            display_name=payload.display_name,
            model_name=payload.model_name,
            base_url=payload.base_url.rstrip("/"),
            api_key_encrypted=encrypt_secret(payload.api_key, self.settings),
            api_key_masked=mask_secret(payload.api_key),
            capabilities_json=dump_json(payload.capabilities),
            parameters_json=dump_json(payload.parameters),
            priority=payload.priority,
            is_default=payload.is_default,
            is_active=payload.is_active,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self.get_model(model.id)

    def update_model(self, model_id: str, payload: ModelUpdate) -> ModelRead:
        model = self._get_model_entity(model_id)
        updates = payload.dict(exclude_unset=True)
        if "provider_id" in updates:
            self._get_provider_entity(updates["provider_id"])
        if updates.get("is_default") is True:
            self._ensure_single_default(model_id=model_id)

        for field, value in updates.items():
            if field == "base_url" and value is not None:
                model.base_url = value.rstrip("/")
            elif field == "api_key":
                model.api_key_encrypted = encrypt_secret(value, self.settings)
                model.api_key_masked = mask_secret(value)
            elif field == "capabilities":
                model.capabilities_json = dump_json(value)
            elif field == "parameters":
                model.parameters_json = dump_json(value)
            else:
                setattr(model, field, value)
        self.db.commit()
        self.db.refresh(model)
        return self._serialize_model(model)

    def delete_model(self, model_id: str) -> None:
        model = self._get_model_entity(model_id)
        self.db.delete(model)
        self.db.commit()

    def run_health_check(self, model_id: str) -> ModelHealthCheckRead:
        model = self._get_model_entity(model_id)
        checked_at = datetime.now(timezone.utc)
        try:
            client = build_llm_client(
                model,
                decrypt_secret(model.api_key_encrypted, self.settings),
                self.settings.default_provider_timeout_seconds,
            )
            result = client.health_check()
            model.health_status = result.status
            detail = result.detail
        except (ProviderRequestError, ValueError) as exc:
            model.health_status = "unhealthy"
            detail = str(exc)

        model.last_checked_at = checked_at
        self.db.commit()
        self.db.refresh(model)
        return ModelHealthCheckRead(
            model_id=model.id,
            status=model.health_status,
            detail=detail,
            checked_at=checked_at,
        )

    def list_policies(self, organization_id: str | None = None, use_case: str | None = None) -> list[PolicyRead]:
        query = self.db.query(db_models.ModelPolicy).order_by(
            db_models.ModelPolicy.organization_id.asc(),
            db_models.ModelPolicy.use_case.asc(),
            db_models.ModelPolicy.updated_at.desc(),
        )
        if organization_id is not None:
            query = query.filter(db_models.ModelPolicy.organization_id == organization_id)
        if use_case:
            query = query.filter(db_models.ModelPolicy.use_case == use_case)
        return [self._serialize_policy(item) for item in query.all()]

    def get_policy(self, policy_id: str) -> PolicyRead:
        policy = self.db.get(db_models.ModelPolicy, policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy khong ton tai.")
        return self._serialize_policy(policy)

    def create_policy(self, payload: PolicyCreate) -> PolicyRead:
        self._get_model_entity(payload.default_model_id)
        if payload.fallback_model_id:
            self._get_model_entity(payload.fallback_model_id)
        policy = db_models.ModelPolicy(
            organization_id=payload.organization_id,
            use_case=payload.use_case,
            default_model_id=payload.default_model_id,
            fallback_model_id=payload.fallback_model_id,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            system_prompt=payload.system_prompt,
            metadata_json=dump_json(payload.metadata),
            is_active=payload.is_active,
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return self._serialize_policy(policy)

    def update_policy(self, policy_id: str, payload: PolicyUpdate) -> PolicyRead:
        policy = self.db.get(db_models.ModelPolicy, policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy khong ton tai.")

        updates = payload.dict(exclude_unset=True)
        if "default_model_id" in updates and updates["default_model_id"] is not None:
            self._get_model_entity(updates["default_model_id"])
        if "fallback_model_id" in updates and updates["fallback_model_id"] is not None:
            self._get_model_entity(updates["fallback_model_id"])

        for field, value in updates.items():
            if field == "metadata":
                policy.metadata_json = dump_json(value)
            else:
                setattr(policy, field, value)
        self.db.commit()
        self.db.refresh(policy)
        return self._serialize_policy(policy)

    def delete_policy(self, policy_id: str) -> None:
        policy = self.db.get(db_models.ModelPolicy, policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy khong ton tai.")
        self.db.delete(policy)
        self.db.commit()

    def resolve_model(
        self,
        model_id: str | None,
        organization_id: str | None,
        use_case: str,
    ) -> tuple[db_models.RegisteredModel, db_models.ModelPolicy | None]:
        if model_id:
            return self._get_model_entity(model_id), None

        policy = (
            self.db.query(db_models.ModelPolicy)
            .options(
                joinedload(db_models.ModelPolicy.default_model).joinedload(db_models.RegisteredModel.provider),
                joinedload(db_models.ModelPolicy.fallback_model).joinedload(db_models.RegisteredModel.provider),
            )
            .filter(
                db_models.ModelPolicy.organization_id == organization_id,
                db_models.ModelPolicy.use_case == use_case,
                db_models.ModelPolicy.is_active.is_(True),
            )
            .order_by(db_models.ModelPolicy.updated_at.desc())
            .first()
        )
        if not policy:
            policy = (
                self.db.query(db_models.ModelPolicy)
                .options(
                    joinedload(db_models.ModelPolicy.default_model).joinedload(db_models.RegisteredModel.provider),
                    joinedload(db_models.ModelPolicy.fallback_model).joinedload(db_models.RegisteredModel.provider),
                )
                .filter(
                    db_models.ModelPolicy.organization_id.is_(None),
                    db_models.ModelPolicy.use_case == use_case,
                    db_models.ModelPolicy.is_active.is_(True),
                )
                .order_by(db_models.ModelPolicy.updated_at.desc())
                .first()
            )
        if policy and policy.default_model and policy.default_model.is_active:
            return policy.default_model, policy

        model = (
            self.db.query(db_models.RegisteredModel)
            .options(joinedload(db_models.RegisteredModel.provider))
            .filter(db_models.RegisteredModel.is_active.is_(True))
            .order_by(db_models.RegisteredModel.is_default.desc(), db_models.RegisteredModel.priority.asc())
            .first()
        )
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong co model active nao de phuc vu inference.",
            )
        return model, policy
