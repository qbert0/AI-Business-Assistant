from sqlalchemy.orm import Session

from app import models
from app.entities import database as db_entities
from app.repositories import users_repository


class UsersService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, payload: models.UserCreate) -> db_entities.User:
        return users_repository.create_user(payload, self.db)

    def list_users(self, search: str | None, skip: int, limit: int) -> list[db_entities.User]:
        return users_repository.list_users(search, skip, limit, self.db)

    def get_user(self, user_id: str) -> db_entities.User:
        return users_repository.get_user(user_id, self.db)
