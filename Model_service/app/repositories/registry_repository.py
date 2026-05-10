from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.configs.runtime_catalog import RuntimeModelEntry, load_runtime_model_catalog
from app.core.config import Settings
from app.core.security import decrypt_secret, encrypt_secret, mask_secret
from app.core.serialization import dump_json, parse_json_dict, parse_json_list
from app.db import models as db_models
from app.dtos.registry_dto import (
    to_model_health_check_model,
    to_model_model,
    to_policy_model,
    to_provider_model,
)
from app.infrastructure.llm.base import ProviderRequestError
from app.infrastructure.llm.factory import build_llm_client
from app.models.registry_model import (
    ModelCreate,
    ModelHealthCheckRead,
    ModelRead,
    ModelUpdate,
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
)
from app.models.provider_model import ProviderCreate, ProviderRead, ProviderUpdate


class RegistryRepository:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    @staticmethod
    def _provider_id(provider_type: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"provider:{provider_type}"))

    @staticmethod
    def _model_id(entry: RuntimeModelEntry) -> str:
        kind = "embedding" if "embedding" in entry.capabilities else "chat"
        return str(uuid5(NAMESPACE_URL, f"model:{kind}:{entry.key}:{entry.model_name}"))

    def sync_models_from_config(self) -> None:
        catalog = load_runtime_model_catalog()
        providers_by_type: dict[str, db_models.Provider] = {}
        expected_model_ids: set[str] = set()

        for entry in catalog.all_models():
            expected_model_ids.add(self._model_id(entry))
            provider = providers_by_type.get(entry.provider_type)
            if provider is None:
                provider = self.db.get(db_models.Provider, self._provider_id(entry.provider_type))
                if provider is None:
                    provider = db_models.Provider(
                        id=self._provider_id(entry.provider_type),
                        name=f"config::{entry.provider_type}",
                        provider_type=entry.provider_type,
                        description="Provider synced from configs/config.yaml",
                        metadata_json=dump_json({"config_managed": True}),
                        is_active=True,
                    )
                    self.db.add(provider)
                else:
                    provider.name = f"config::{entry.provider_type}"
                    provider.provider_type = entry.provider_type
                    provider.description = "Provider synced from configs/config.yaml"
                    provider.metadata_json = dump_json({"config_managed": True})
                    provider.is_active = True
                providers_by_type[entry.provider_type] = provider

            model = self.db.get(db_models.RegisteredModel, self._model_id(entry))
            if model is None:
                model = db_models.RegisteredModel(
                    id=self._model_id(entry),
                    provider_id=provider.id,
                    display_name=entry.key,
                    model_name=entry.model_name,
                    base_url=entry.base_url,
                    api_key_encrypted=encrypt_secret(entry.api_key, self.settings),
                    api_key_masked=mask_secret(entry.api_key),
                    capabilities_json=dump_json(entry.capabilities),
                    parameters_json=dump_json(entry.parameters),
                    priority=100,
                    is_default=entry.is_default,
                    is_active=True,
                    health_status="unknown",
                )
                self.db.add(model)
            else:
                model.provider_id = provider.id
                model.display_name = entry.key
                model.model_name = entry.model_name
                model.base_url = entry.base_url
                model.api_key_encrypted = encrypt_secret(entry.api_key, self.settings)
                model.api_key_masked = mask_secret(entry.api_key)
                model.capabilities_json = dump_json(entry.capabilities)
                model.parameters_json = dump_json(entry.parameters)
                model.is_default = entry.is_default
                model.is_active = True

        for model in self.db.query(db_models.RegisteredModel).all():
            parameters = parse_json_dict(model.parameters_json)
            if parameters.get("config_managed") is True and model.id not in expected_model_ids:
                model.is_active = False
                model.is_default = False

        self.db.commit()

    def _find_model_by_name(self, name: str) -> db_models.RegisteredModel | None:
        candidates = (
            self.db.query(db_models.RegisteredModel)
            .options(joinedload(db_models.RegisteredModel.provider))
            .filter(
                db_models.RegisteredModel.is_active.is_(True),
                or_(
                    db_models.RegisteredModel.display_name == name,
                    db_models.RegisteredModel.model_name == name,
                ),
            )
            .order_by(db_models.RegisteredModel.is_default.desc(), db_models.RegisteredModel.priority.asc())
            .all()
        )
        for candidate in candidates:
            if parse_json_dict(candidate.parameters_json).get("config_managed") is True:
                return candidate
        return None

    def resolve_runtime_model(
        self,
        *,
        model_id: str | None,
        model_name: str | None,
        kind: str,
    ) -> db_models.RegisteredModel:
        catalog = load_runtime_model_catalog()

        if model_id:
            model = self._get_model_entity(model_id)
        else:
            requested_name = model_name
            if not requested_name:
                requested_name = (
                    catalog.default_embedding_model if kind == "embedding" else catalog.default_llm_model
                )
            if not requested_name:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Khong co default {kind} model trong configs/config.yaml.",
                )
            model = self._find_model_by_name(requested_name)
            if model is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Model '{requested_name}' khong ton tai trong configs/config.yaml.",
                )

        capabilities = parse_json_list(model.capabilities_json)
        required_capability = "embedding" if kind == "embedding" else "chat"
        if required_capability not in capabilities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model '{model.display_name}' khong ho tro capability '{required_capability}'.",
            )
        return model

    def _serialize_provider(self, provider: db_models.Provider) -> ProviderRead:
        return to_provider_model(provider)

    def _serialize_model(self, model: db_models.RegisteredModel) -> ModelRead:
        return to_model_model(model)

    def _serialize_policy(self, policy: db_models.ModelPolicy) -> PolicyRead:
        return to_policy_model(policy)

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
        return to_model_health_check_model(model.id, model.health_status, detail, checked_at)

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
            .filter(
                db_models.RegisteredModel.is_active.is_(True),
                db_models.RegisteredModel.capabilities_json.like('%"chat"%'),
            )
            .order_by(db_models.RegisteredModel.is_default.desc(), db_models.RegisteredModel.priority.asc())
            .first()
        )
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong co chat model active nao de phuc vu inference.",
            )
        return model, policy
