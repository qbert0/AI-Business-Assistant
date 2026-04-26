from app.core.config import Settings
from app.core.security import decrypt_secret, encrypt_secret, mask_secret


def test_encrypt_and_decrypt_secret_round_trip() -> None:
    settings = Settings(model_service_secret_key="unit-test-secret")
    secret = "sk-example-1234567890"

    encrypted = encrypt_secret(secret, settings)

    assert encrypted is not None
    assert encrypted != secret
    assert decrypt_secret(encrypted, settings) == secret


def test_mask_secret_keeps_prefix_and_suffix() -> None:
    masked = mask_secret("sk-example-1234567890")
    assert masked == "sk-e...7890"
