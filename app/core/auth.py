import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.settings import settings


def _derive_key(key_material: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(key_material.encode()))


def encrypt_token(token: str) -> str:
    salt = os.urandom(16)
    key = _derive_key(settings.encryption_key, salt)
    f = Fernet(key)
    encrypted = f.encrypt(token.encode())
    return base64.urlsafe_b64encode(salt + encrypted).decode()


def decrypt_token(encrypted_token: str) -> str:
    raw = base64.urlsafe_b64decode(encrypted_token.encode())
    salt = raw[:16]
    payload = raw[16:]
    key = _derive_key(settings.encryption_key, salt)
    f = Fernet(key)
    return f.decrypt(payload).decode()
