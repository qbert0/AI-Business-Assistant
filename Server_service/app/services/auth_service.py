from sqlalchemy.orm import Session

from app import models
from app.entities.api import TokenEntity
from app.repositories import auth_repository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register(self, payload: models.AuthRegister) -> TokenEntity:
        return auth_repository.register(payload, self.db)

    def login(self, payload: models.AuthLogin) -> TokenEntity:
        return auth_repository.login(payload, self.db)
