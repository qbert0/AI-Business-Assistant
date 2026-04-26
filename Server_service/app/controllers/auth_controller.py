from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.dtos import auth_dto, common_dto
from app.entities import database as db_entities
from app.repositories import auth_repository
from app.services.security import get_current_user

router = APIRouter()


@router.post("/auth/register", response_model=models.TokenResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"], summary="Dang ky va nhan JWT")
def register(payload: models.AuthRegister, db: Session = Depends(get_db)) -> models.TokenResponse:
    token = auth_repository.register(payload, db)
    return auth_dto.to_token_model(token)


@router.post("/auth/login", response_model=models.TokenResponse, tags=["Auth"], summary="Dang nhap bang email/password va nhan JWT")
def login(payload: models.AuthLogin, db: Session = Depends(get_db)) -> models.TokenResponse:
    token = auth_repository.login(payload, db)
    return auth_dto.to_token_model(token)


@router.get("/auth/me", response_model=models.UserRead, tags=["Auth"], summary="Lay user hien tai tu Bearer JWT")
def auth_me(current_user: db_entities.User = Depends(get_current_user)) -> models.UserRead:
    return common_dto.to_user_model(current_user)
