import os
from fastapi import FastAPI, Request, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.settings import settings
from app.storage.db import get_db, init_db
from app.storage.repository import AccountRepository
from app.storage.models import User
from app.monitoring.metrics import get_metrics
from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router
from app.core.security import decode_access_token

init_db()

from app.jobs.scheduler import start_scheduler
start_scheduler()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(api_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return RedirectResponse(url="/auth/login")

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    token: str = Query(""),
    db: Session = Depends(get_db),
):
    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if token:
        try:
            payload = decode_access_token(token)
            user = db.query(User).filter(User.id == int(payload["sub"])).first()
        except Exception:
            pass

    if not user:
        return RedirectResponse(url="/auth/login")

    from app.jobs.cleanup import auto_cleanup
    auto_cleanup()

    stats = get_metrics(db, user_id=user.id)

    from app.storage.models import EmailRecord, PredictionRecord

    query_results = (
        db.query(EmailRecord, PredictionRecord)
        .outerjoin(PredictionRecord, EmailRecord.id == PredictionRecord.email_id)
        .filter(EmailRecord.user_id == user.id)
        .order_by(desc(EmailRecord.received_at))
        .limit(50)
        .all()
    )

    recent_emails = []
    for email, pred in query_results:
        is_sent = bool(email.is_sent)
        recent_emails.append({
            "id": email.id,
            "sender": email.sender,
            "recipients": email.recipients or "",
            "subject": email.subject or "(No Subject)",
            "body_text": email.body_text or "No message body found.",
            "received_at": email.received_at.strftime("%Y-%m-%d %H:%M:%S") if email.received_at else "Unknown",
            "spam_label": pred.spam_label if pred else ("sent" if is_sent else "pending"),
            "category_label": pred.category_label if pred else ("sent" if is_sent else "pending"),
            "priority_score": 0.0,
            "routed_folder": pred.routed_folder if pred else ("Sent" if is_sent else "Inbox"),
            "routed_action": pred.routed_action if pred else ("none" if is_sent else "pending"),
            "is_sent": is_sent,
            "in_reply_to_id": email.in_reply_to_id,
        })

    default_acc = AccountRepository(db).get_default_account_for_user(user.id)
    default_email = default_acc.email if default_acc else (settings.smtp_default_sender or settings.smtp_user or "")

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "stats": stats,
            "recent_emails": recent_emails,
            "default_account_email": default_email,
            "token": token,
            "user_email": user.email,
        }
    )


@app.get("/auth/login", response_class=HTMLResponse)
def login_page(request: Request, token: str = Query("")):
    if token:
        try:
            decode_access_token(token)
            return RedirectResponse(url="/dashboard")
        except Exception:
            pass
    return templates.TemplateResponse(request=request, name="login.html")


connected_clients = {}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query("")):
    await websocket.accept()
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4001)
        return

    if user_id not in connected_clients:
        connected_clients[user_id] = []
    connected_clients[user_id].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if user_id in connected_clients:
            connected_clients[user_id].remove(websocket)


def notify_user(user_id: int, event: dict):
    import json
    import asyncio
    for ws in connected_clients.get(user_id, []):
        try:
            asyncio.create_task(ws.send_json(event))
        except Exception:
            pass
