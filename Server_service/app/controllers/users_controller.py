from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.dtos import common_dto
from app.services import UsersService

router = APIRouter()


@router.post("/users", response_model=models.UserRead, status_code=status.HTTP_201_CREATED, tags=["Users"], summary="Tao user moi")
def create_user(payload: models.UserCreate, db: Session = Depends(get_db)) -> models.UserRead:
    user = UsersService(db).create_user(payload)
    return common_dto.to_user_model(user)


@router.get("/users", response_model=list[models.UserRead], tags=["Users"], summary="Lay danh sach user")
def list_users(
    search: str | None = Query(None, description="Tim theo email hoac ten."),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[models.UserRead]:
    users = UsersService(db).list_users(search, skip, limit)
    return [common_dto.to_user_model(user) for user in users]


@router.get("/users/{user_id}", response_model=models.UserRead, tags=["Users"], summary="Lay chi tiet user")
def get_user(user_id: str, db: Session = Depends(get_db)) -> models.UserRead:
    user = UsersService(db).get_user(user_id)
    return common_dto.to_user_model(user)
