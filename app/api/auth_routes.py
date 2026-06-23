import os
import threading
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.storage.db import get_db
from app.storage.models import User
from app.core.security import (
    verify_password, hash_password, create_access_token,
    get_current_user, require_user, decode_access_token,
)
from app.storage.repository import ContainerRepository, AccountRepository

router = APIRouter(prefix="/auth", tags=["auth"])
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))


class RegisterRequest(BaseModel):
    email: str
    password: str
    gmail_email: Optional[str] = None
    gmail_app_password: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    user = User(email=req.email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    ContainerRepository(db).seed_for_user(user.id)
    gmail = req.gmail_email or req.email
    acc = AccountRepository(db).create_account(
        email=gmail,
        imap_host="imap.gmail.com", imap_port=993, imap_user=gmail,
        imap_password=req.gmail_app_password,
        imap_use_ssl=True,
        smtp_host="smtp.gmail.com", smtp_port=587, smtp_user=gmail,
        smtp_password=req.gmail_app_password,
        smtp_use_tls=True,
        is_default=True, user_id=user.id,
    )
    token = create_access_token({"sub": str(user.id)})
    if req.gmail_app_password:
        def _initial_sync(aid: int):
            try:
                from app.jobs.sync_job import sync_account
                sync_account(aid)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error("Background initial sync failed: %s", e)
        threading.Thread(target=_initial_sync, args=(acc.id,), daemon=True).start()
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email}}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email}}


@router.get("/me")
def me(current_user: User = Depends(require_user)):
    return {"id": current_user.id, "email": current_user.email}


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, token: str = Query("")):
    if token:
        try:
            decode_access_token(token)
            return RedirectResponse(url="/dashboard")
        except Exception:
            pass
    return templates.TemplateResponse(request=request, name="login.html")
