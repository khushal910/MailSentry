import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def _get_fernet_instance() -> Fernet:
    """
    Derives a deterministic 32-byte Fernet key from settings.SECRET_KEY.
    """
    secret = settings.SECRET_KEY or "default-mailsentry-secret-key"
    hashed = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(hashed)
    return Fernet(key)

def encrypt_token(plain_token: str) -> str:
    """
    Symmetrically encrypts a token string (e.g. refresh_token) using Fernet.
    """
    if not plain_token:
        return ""
    fernet = _get_fernet_instance()
    encrypted_bytes = fernet.encrypt(plain_token.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypts a Fernet encrypted token string.
    """
    if not encrypted_token:
        return ""
    fernet = _get_fernet_instance()
    decrypted_bytes = fernet.decrypt(encrypted_token.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
