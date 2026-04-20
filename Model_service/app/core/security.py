import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings


def _build_fernet(settings: Settings) -> Fernet:
    digest = hashlib.sha256(settings.model_service_secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(secret: str | None, settings: Settings) -> str | None:
    if not secret:
        return None
    return _build_fernet(settings).encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_secret: str | None, settings: Settings) -> str | None:
    if not encrypted_secret:
        return None
    try:
        return _build_fernet(settings).decrypt(encrypted_secret.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Stored API key cannot be decrypted with the current secret key.") from exc


def mask_secret(secret: str | None) -> str | None:
    if not secret:
        return None
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"
