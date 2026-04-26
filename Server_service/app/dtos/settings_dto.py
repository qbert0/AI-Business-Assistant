from app import models
from app.dtos.common_dto import to_organization_model
from app.entities.api import OrganizationSettingsEntity


def to_organization_settings_model(entity: OrganizationSettingsEntity) -> models.OrganizationSettingsRead:
    return models.OrganizationSettingsRead(
        organization=to_organization_model(entity.organization),
        settings=entity.settings,
    )
