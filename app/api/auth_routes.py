from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from app.core.auth import (
    get_gmail_oauth_url, get_outlook_oauth_url,
    exchange_gmail_code, exchange_outlook_code,
)
from app.storage.db import SessionLocal
from app.storage.repository import AccountRepository, AuditLogRepository
import json

router = APIRouter(prefix="/auth", tags=["auth"])

OAUTH_SUCCESS_PAGE = """
<!DOCTYPE html>
<html><body style="font-family:sans-serif;padding:40px;text-align:center">
<h2 style="color:#1a73e8">OAuth2 Authorization Successful</h2>
<p>Your Google account has been connected. You can close this tab or <a href="/dashboard" style="color:#1a73e8">return to dashboard</a>.</p>
<script>setTimeout(function(){ window.location.href='/dashboard'; }, 2000);</script>
</body></html>
"""


@router.get("/gmail/login")
def gmail_login(email: str = Query("")):
    url = get_gmail_oauth_url(state=email)
    return RedirectResponse(url)


@router.get("/gmail/callback")
def gmail_callback(code: str = Query(...), state: str = Query("")):
    try:
        token_data = exchange_gmail_code(code)
        token_json = json.dumps(token_data)

        db = SessionLocal()
        try:
            if state:
                repo = AccountRepository(db)
                ok = repo.set_gmail_token(state, token_json)
                if ok:
                    AuditLogRepository(db).log(
                        email_id=None, event_type="gmail_oauth_connected",
                        payload={"email": state},
                    )
        finally:
            db.close()

        return HTMLResponse(content=OAUTH_SUCCESS_PAGE)
    except Exception as e:
        raise HTTPException(400, f"Gmail OAuth2 failed: {e}")


@router.get("/outlook/login")
def outlook_login(email: str = Query("")):
    url = get_outlook_oauth_url()
    return RedirectResponse(url)


@router.get("/outlook/callback")
def outlook_callback(code: str = Query(...)):
    try:
        token_data = exchange_outlook_code(code)
        return HTMLResponse(content=OAUTH_SUCCESS_PAGE)
    except Exception as e:
        raise HTTPException(400, f"Outlook OAuth2 failed: {e}")
