import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import messages
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.entities import database as db_entities
from app.entities.api import TokenEntity
from app.services.security import create_access_token, hash_password, verify_password
from app.utils.constants import GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET


def _extract_google_error(exc: httpx.HTTPStatusError) -> str:
    try:
        payload = exc.response.json()
    except ValueError:
        return exc.response.text or str(exc)

    error = str(payload.get("error") or "").strip()
    description = str(payload.get("error_description") or "").strip()
    if error and description:
        return f"{error}: {description}"
    return error or description or exc.response.text or str(exc)


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


def login_with_google(payload, db: Session) -> TokenEntity:
    if not GOOGLE_OAUTH_CLIENT_ID or not GOOGLE_OAUTH_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=messages.GOOGLE_AUTH_NOT_CONFIGURED,
        )

    try:
        with httpx.Client(timeout=15.0) as client:
            token_response = client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": payload.code,
                    "client_id": GOOGLE_OAUTH_CLIENT_ID,
                    "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                    "redirect_uri": payload.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            token_data = token_response.json()

            id_token = token_data.get("id_token")
            access_token = token_data.get("access_token")
            if not id_token or not access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=messages.GOOGLE_AUTH_INVALID_TOKEN,
                )

            token_info_response = client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
            )
            token_info_response.raise_for_status()
            token_info = token_info_response.json()
            if token_info.get("aud") != GOOGLE_OAUTH_CLIENT_ID:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=messages.GOOGLE_AUTH_INVALID_TOKEN,
                )

            user_info_response = client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{messages.GOOGLE_AUTH_EXCHANGE_FAILED} ({_extract_google_error(exc)})",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=messages.GOOGLE_AUTH_EXCHANGE_FAILED,
        ) from exc

    email = str(user_info.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=messages.GOOGLE_AUTH_INVALID_TOKEN,
        )

    if user_info.get("email_verified") is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=messages.GOOGLE_AUTH_EMAIL_NOT_VERIFIED,
        )

    user = db.query(db_entities.User).filter(db_entities.User.email == email).first()
    if not user:
        user = db_entities.User(
            email=email,
            full_name=str(user_info.get("name") or email.split("@", 1)[0]),
            avatar_url=user_info.get("picture"),
            password_hash=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        updated = False
        full_name = str(user_info.get("name") or "").strip()
        avatar_url = user_info.get("picture")
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            updated = True
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if updated:
            db.add(user)
            db.commit()
            db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.USER_DISABLED)

    return TokenEntity(
        access_token=create_access_token(user),
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )
