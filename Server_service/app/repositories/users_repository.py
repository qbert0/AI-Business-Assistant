from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import messages
from app import models
from app.entities import database as db_entities
from app.repositories.common import get_user_or_404
from app.services.security import hash_password


def create_user(payload: models.UserCreate, db: Session) -> db_entities.User:
    existing = db.query(db_entities.User).filter(db_entities.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.EMAIL_ALREADY_REGISTERED)
    user = db_entities.User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password) if payload.password else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(search: str | None, skip: int, limit: int, db: Session) -> list[db_entities.User]:
    query = db.query(db_entities.User)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(db_entities.User.email.like(like), db_entities.User.full_name.like(like)))
    return query.order_by(db_entities.User.created_at.desc()).offset(skip).limit(limit).all()


def get_user(user_id: str, db: Session) -> db_entities.User:
    return get_user_or_404(db, user_id)
