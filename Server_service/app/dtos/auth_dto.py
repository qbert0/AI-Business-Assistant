from app import models
from app.dtos.common_dto import to_user_model
from app.entities.api import TokenEntity


def to_token_model(entity: TokenEntity) -> models.TokenResponse:
    return models.TokenResponse(
        access_token=entity.access_token,
        token_type=entity.token_type,
        expires_in_seconds=entity.expires_in_seconds,
        user=to_user_model(entity.user),
    )
