from app.core.config import Settings
from app.models.provider_model import ProviderCreate, ProviderRead, ProviderUpdate
from app.models.registry_model import (
    ModelCreate,
    ModelHealthCheckRead,
    ModelRead,
    ModelUpdate,
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
)
from app.repositories.registry_repository import RegistryRepository


class RegistryService:
    def __init__(self, repository: RegistryRepository) -> None:
        self.repository = repository

    @classmethod
    def from_dependencies(cls, db, settings: Settings) -> "RegistryService":
        return cls(RegistryRepository(db, settings))

    def list_providers(self, name: str | None = None) -> list[ProviderRead]:
        return self.repository.list_providers(name=name)

    def get_provider(self, provider_id: str) -> ProviderRead:
        return self.repository.get_provider(provider_id)

    def create_provider(self, payload: ProviderCreate) -> ProviderRead:
        return self.repository.create_provider(payload)

    def update_provider(self, provider_id: str, payload: ProviderUpdate) -> ProviderRead:
        return self.repository.update_provider(provider_id, payload)

    def delete_provider(self, provider_id: str) -> None:
        self.repository.delete_provider(provider_id)

    def list_models(
        self,
        *,
        provider_id: str | None = None,
        provider_name: str | None = None,
        model_name: str | None = None,
        is_active: bool | None = None,
    ) -> list[ModelRead]:
        return self.repository.list_models(
            provider_id=provider_id,
            provider_name=provider_name,
            model_name=model_name,
            is_active=is_active,
        )

    def get_model(self, model_id: str) -> ModelRead:
        return self.repository.get_model(model_id)

    def create_model(self, payload: ModelCreate) -> ModelRead:
        return self.repository.create_model(payload)

    def update_model(self, model_id: str, payload: ModelUpdate) -> ModelRead:
        return self.repository.update_model(model_id, payload)

    def delete_model(self, model_id: str) -> None:
        self.repository.delete_model(model_id)

    def run_health_check(self, model_id: str) -> ModelHealthCheckRead:
        return self.repository.run_health_check(model_id)

    def list_policies(
        self,
        *,
        organization_id: str | None = None,
        use_case: str | None = None,
    ) -> list[PolicyRead]:
        return self.repository.list_policies(organization_id=organization_id, use_case=use_case)

    def get_policy(self, policy_id: str) -> PolicyRead:
        return self.repository.get_policy(policy_id)

    def create_policy(self, payload: PolicyCreate) -> PolicyRead:
        return self.repository.create_policy(payload)

    def update_policy(self, policy_id: str, payload: PolicyUpdate) -> PolicyRead:
        return self.repository.update_policy(policy_id, payload)

    def delete_policy(self, policy_id: str) -> None:
        self.repository.delete_policy(policy_id)
