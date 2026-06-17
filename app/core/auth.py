import base64
import os
import json
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import HTTPException
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


def store_oauth_token(provider: str, token_data: dict):
    from app.storage.db import SessionLocal
    from app.storage.repository import AuditLogRepository
    encrypted = encrypt_token(json.dumps(token_data))
    db = SessionLocal()
    try:
        AuditLogRepository(db).log(
            email_id=None, event_type=f"oauth_token_stored",
            payload={"provider": provider},
        )
    finally:
        db.close()
    return encrypted


def get_gmail_oauth_url(state: str = "") -> str:
    if not all([settings.gmail_client_id, settings.gmail_client_secret, settings.gmail_redirect_uri]):
        raise HTTPException(500, "Gmail OAuth2 not configured")
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.gmail_redirect_uri],
            }
        },
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
        redirect_uri=settings.gmail_redirect_uri,
    )
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline",
                                          include_granted_scopes="true", state=state)
    return auth_url


def get_outlook_oauth_url() -> str:
    if not all([settings.outlook_client_id, settings.outlook_redirect_uri]):
        raise HTTPException(500, "Outlook OAuth2 not configured")
    params = {
        "client_id": settings.outlook_client_id,
        "response_type": "code",
        "redirect_uri": settings.outlook_redirect_uri,
        "scope": "User.Read Mail.ReadWrite Mail.Send offline_access",
        "response_mode": "query",
    }
    from urllib.parse import urlencode
    tenant = settings.outlook_tenant
    return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?{urlencode(params)}"


def exchange_gmail_code(code: str) -> dict:
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.gmail_redirect_uri],
            }
        },
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
        redirect_uri=settings.gmail_redirect_uri,
    )
    flow.fetch_token(code=code)
    return {
        "token": flow.credentials.token,
        "refresh_token": flow.credentials.refresh_token,
        "expiry": flow.credentials.expiry.isoformat() if flow.credentials.expiry else None,
    }


def exchange_outlook_code(code: str) -> dict:
    import requests
    tenant = settings.outlook_tenant
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "client_id": settings.outlook_client_id,
        "client_secret": settings.outlook_client_secret,
        "code": code,
        "redirect_uri": settings.outlook_redirect_uri,
        "grant_type": "authorization_code",
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()
