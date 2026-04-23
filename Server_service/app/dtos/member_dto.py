from app import models
from app.dtos.common_dto import to_member_model
from app.entities import database as db_entities


def to_member_models(members: list[db_entities.OrganizationMember]) -> list[models.MemberRead]:
    return [to_member_model(member) for member in members]
