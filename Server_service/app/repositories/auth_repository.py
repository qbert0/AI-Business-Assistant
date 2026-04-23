from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import messages
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.entities import database as db_entities
from app.entities.api import TokenEntity
from app.services.security import create_access_token, hash_password, verify_password


def register(payload, db: Session) -> TokenEntity:
    existing = db.query(db_entities.User).filter(db_entities.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.EMAIL_ALREADY_REGISTERED)

    user = db_entities.User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenEntity(
        access_token=create_access_token(user),
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


def login(payload, db: Session) -> TokenEntity:
    user = db.query(db_entities.User).filter(db_entities.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_CREDENTIALS)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_DISABLED)
    return TokenEntity(
        access_token=create_access_token(user),
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )
