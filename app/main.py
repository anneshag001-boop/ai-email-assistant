import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.settings import settings
from app.storage.db import get_db, init_db
from app.storage.repository import AccountRepository
from app.monitoring.metrics import get_metrics
from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router

init_db()

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(api_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard")

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    from app.jobs.cleanup import auto_cleanup
    auto_cleanup()

    stats = get_metrics(db)

    from app.storage.models import EmailRecord, PredictionRecord

    query_results = (
        db.query(EmailRecord, PredictionRecord)
        .outerjoin(PredictionRecord, EmailRecord.id == PredictionRecord.email_id)
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

    default_acc = AccountRepository(db).get_default_account()
    default_email = default_acc.email if default_acc else (settings.smtp_default_sender or settings.smtp_user or "")

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "stats": stats,
            "recent_emails": recent_emails,
            "default_account_email": default_email,
        }
    )
