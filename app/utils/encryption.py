"""Encryption / decryption utilities with robust error handling."""
import logging
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

logger = logging.getLogger(__name__)

_cipher: Fernet | None = None
_cipher_error: str | None = None


def _get_cipher() -> Fernet:
    """Lazily initialise and cache the Fernet cipher.

    Raises ValueError with a clear message if ENCRYPTION_KEY is missing
    or invalid — callers should catch this and return a user-friendly error.
    """
    global _cipher, _cipher_error
    if _cipher is not None:
        return _cipher
    if _cipher_error is not None:
        raise ValueError(_cipher_error)

    key = settings.ENCRYPTION_KEY
    if not key:
        _cipher_error = (
            "ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
        logger.error(_cipher_error)
        raise ValueError(_cipher_error)

    try:
        _cipher = Fernet(key)
        logger.debug("Fernet cipher initialised successfully")
        return _cipher
    except Exception as e:
        _cipher_error = f"ENCRYPTION_KEY is invalid: {e}. Generate a valid key with Fernet.generate_key()"
        logger.error(_cipher_error)
        raise ValueError(_cipher_error)


def encrypt_api_key(value: str) -> str:
    """Encrypt an API key value for database storage."""
    if not value:
        raise ValueError("Cannot encrypt empty key value")
    cipher = _get_cipher()
    return cipher.encrypt(value.encode()).decode()


def decrypt_api_key(encrypted_value: str) -> str:
    """Decrypt an API key value from database storage.

    Raises ValueError if the encrypted value is corrupt/tampered, or if
    the encryption key has changed since the value was encrypted.
    """
    if not encrypted_value:
        raise ValueError("Cannot decrypt empty value")
    cipher = _get_cipher()
    try:
        return cipher.decrypt(encrypted_value.encode()).decode()
    except InvalidToken:
        logger.exception("Failed to decrypt API key — key rotation or data corruption?")
        raise ValueError(
            "Failed to decrypt API key. The encryption key may have changed "
            "since the key was stored. Please re-add your API keys."
        )
