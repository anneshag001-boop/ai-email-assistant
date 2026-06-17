import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.storage.db import get_db
from app.storage.repository import EmailRepository, PredictionRepository, AuditLogRepository, AccountRepository, ContainerRepository
from app.storage.models import EmailRecord, PredictionRecord
from app.api.schemas import (
    IngestEmailRequest, IngestEmailResponse, ClassifyResponse,
    FeedbackRequest, FeedbackResponse, EmailOut, MetricsResponse,
    RetrainResponse, CleanupResponse, ComposeRequest, ReplyRequest, ComposeResponse,
    AccountIn, AccountOut, ContainerIn, ContainerOut, ActivityOut,
)
from app.preprocessing.cleaner import clean_body
from app.ai.spam_detector import SpamDetector
from app.ai.classifier import EmailClassifier
from app.ai.scorer import compute_confidence
from app.routing.router import route_email
from app.feedback.capture import capture_feedback
from app.monitoring.metrics import get_metrics
from app.jobs.cleanup import move_spam_to_trash, cleanup_trash_all, auto_cleanup
from app.jobs.sync_job import sync_account, sync_gmail_oauth
from app.core.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])


def _resolve_sender(db: Session) -> str:
    default = AccountRepository(db).get_default_account()
    if default:
        return default.email
    return settings.smtp_default_sender or settings.smtp_user or "user@localhost"


def _send_smtp(to: str, subject: str, body: str, sender: str = "") -> bool:
    acc_user = settings.smtp_user
    acc_pass = settings.smtp_password
    if not acc_user or not acc_pass:
        logger.warning("SMTP not configured — email logged but not sent")
        return False
    msg = MIMEMultipart()
    msg["From"] = sender or settings.smtp_default_sender or acc_user
    msg["To"] = to
    msg["Subject"] = subject or "(No Subject)"
    msg.attach(MIMEText(body or "", "plain"))
    try:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        if settings.smtp_use_tls:
            server.starttls()
        server.login(acc_user, acc_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        return False


def _account_to_out(acc) -> dict:
    return {
        "id": acc.id,
        "email": acc.email,
        "smtp_host": acc.smtp_host or "smtp.gmail.com",
        "smtp_port": acc.smtp_port or 587,
        "smtp_user": acc.smtp_user,
        "smtp_use_tls": bool(acc.smtp_use_tls),
        "imap_host": acc.imap_host or "imap.gmail.com",
        "imap_port": acc.imap_port or 993,
        "imap_user": acc.imap_user,
        "imap_use_ssl": bool(acc.imap_use_ssl),
        "has_imap_password": bool(acc.imap_password),
        "gmail_connected": bool(acc.gmail_token),
        "is_default": bool(acc.is_default),
        "created_at": acc.created_at.isoformat() if acc.created_at else None,
    }


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db)):
    accounts = AccountRepository(db).list_accounts()
    return [_account_to_out(a) for a in accounts]


@router.post("/accounts")
def create_account(req: AccountIn, db: Session = Depends(get_db)):
    acc = AccountRepository(db).create_account(
        email=req.email, smtp_host=req.smtp_host, smtp_port=req.smtp_port,
        smtp_user=req.smtp_user, smtp_password=req.smtp_password,
        smtp_use_tls=req.smtp_use_tls,
        imap_host=req.imap_host, imap_port=req.imap_port,
        imap_user=req.imap_user, imap_password=req.imap_password,
        imap_use_ssl=req.imap_use_ssl,
        is_default=req.is_default,
    )
    return _account_to_out(acc)


@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    ok = AccountRepository(db).delete_account(account_id)
    if not ok:
        raise HTTPException(404, "Account not found")
    return {"status": "deleted"}


@router.put("/accounts/{account_id}/default")
def set_default_account(account_id: int, db: Session = Depends(get_db)):
    account = AccountRepository(db).set_default(account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    return _account_to_out(account)


@router.post("/accounts/{account_id}/sync")
def sync_account_emails(account_id: int, db: Session = Depends(get_db)):
    result = sync_account(account_id)
    if result["status"] == "error":
        raise HTTPException(400, result["message"])
    return result


@router.get("/accounts/{account_id}/gmail-auth-url")
def get_gmail_auth_url(account_id: int, db: Session = Depends(get_db)):
    repo = AccountRepository(db)
    account = repo.get_account(account_id)
    if not account:
        raise HTTPException(404, "Account not found")
    from app.core.auth import get_gmail_oauth_url
    url = get_gmail_oauth_url(state=account.email)
    return {"url": url}


@router.post("/accounts/{account_id}/sync-gmail")
def sync_gmail_emails(account_id: int, db: Session = Depends(get_db)):
    result = sync_gmail_oauth(account_id)
    if result["status"] == "error":
        raise HTTPException(400, result["message"])
    return result


@router.get("/containers", response_model=List[ContainerOut])
def list_containers(db: Session = Depends(get_db)):
    return ContainerRepository(db).list_all()


@router.post("/containers", response_model=ContainerOut, status_code=201)
def create_container(req: ContainerIn, db: Session = Depends(get_db)):
    return ContainerRepository(db).create(req.name)


@router.delete("/containers/{container_id}")
def delete_container(container_id: int, db: Session = Depends(get_db)):
    ok = ContainerRepository(db).delete(container_id)
    if not ok:
        raise HTTPException(400, "Cannot delete default container or not found")
    return {"status": "deleted"}


@router.post("/compose", response_model=ComposeResponse)
def compose_email(req: ComposeRequest, db: Session = Depends(get_db)):
    sender = _resolve_sender(db)
    repo = EmailRepository(db)
    email = repo.save_sent_email(
        sender=sender,
        recipients=req.to,
        subject=req.subject,
        body_text=req.body,
        in_reply_to_id=None,
    )
    pred = PredictionRecord(
        email_id=email.id,
        spam_score=0.0,
        spam_label="ham",
        category_label="sent",
        category_confidence=1.0,
        priority_score=0.0,
        routed_folder="Sent",
        routed_action="none",
    )
    PredictionRepository(db).save_prediction(pred)

    smtp_ok = _send_smtp(req.to, req.subject, req.body, sender)
    AuditLogRepository(db).log(
        email_id=email.id,
        event_type="email_sent",
        payload={"to": req.to, "subject": req.subject, "smtp_delivered": smtp_ok},
    )
    return ComposeResponse(email_id=email.id, status="sent" if smtp_ok else "queued")


@router.post("/drafts", response_model=ComposeResponse)
def save_draft(req: ComposeRequest, db: Session = Depends(get_db)):
    sender = _resolve_sender(db)
    repo = EmailRepository(db)
    email = repo.save_draft(
        sender=sender,
        recipients=req.to,
        subject=req.subject,
        body_text=req.body,
    )
    AuditLogRepository(db).log(
        email_id=email.id,
        event_type="draft_saved",
        payload={"to": req.to, "subject": req.subject},
    )
    return ComposeResponse(email_id=email.id, status="draft_saved")


@router.post("/reply/{email_id}", response_model=ComposeResponse)
def reply_to_email(email_id: int, req: ReplyRequest, db: Session = Depends(get_db)):
    original = EmailRepository(db).get_email(email_id)
    if not original:
        raise HTTPException(404, "Original email not found")

    sender = _resolve_sender(db)
    repo = EmailRepository(db)
    email = repo.save_sent_email(
        sender=sender,
        recipients=original.sender,
        subject=f"Re: {original.subject or ''}",
        body_text=req.body,
        in_reply_to_id=email_id,
    )
    pred = PredictionRecord(
        email_id=email.id,
        spam_score=0.0,
        spam_label="ham",
        category_label="sent",
        category_confidence=1.0,
        priority_score=0.0,
        routed_folder="Sent",
        routed_action="none",
    )
    PredictionRepository(db).save_prediction(pred)

    smtp_ok = _send_smtp(original.sender, f"Re: {original.subject or ''}", req.body, sender)
    AuditLogRepository(db).log(
        email_id=email.id,
        event_type="email_replied",
        payload={
            "in_reply_to": email_id,
            "to": original.sender,
            "subject": f"Re: {original.subject or ''}",
            "smtp_delivered": smtp_ok,
        },
    )
    return ComposeResponse(email_id=email.id, status="sent" if smtp_ok else "queued")


@router.post("/ingest/email", response_model=IngestEmailResponse)
def ingest_email(req: IngestEmailRequest, db: Session = Depends(get_db)):
    email_repo = EmailRepository(db)
    existing = email_repo.get_email_by_message_id(req.message_id, req.provider)
    if existing:
        return IngestEmailResponse(email_id=existing.id, message_id=req.message_id, status="duplicate")

    saved = email_repo.save_email(EmailRecord(
        provider=req.provider, message_id=req.message_id, sender=req.sender,
        recipients=req.recipients, subject=req.subject,
        body_text=clean_body(req.body_text, req.body_html),
        body_html=req.body_html, received_at=req.received_at,
        thread_id=req.thread_id, attachments_count=req.attachments_count,
    ))
    AuditLogRepository(db).log(email_id=saved.id, event_type="email_ingested",
                                payload={"message_id": req.message_id})
    return IngestEmailResponse(email_id=saved.id, message_id=req.message_id, status="ingested")


@router.post("/classify/email", response_model=ClassifyResponse)
def classify_email(email_id: int = Query(...), db: Session = Depends(get_db)):
    email = EmailRepository(db).get_email(email_id)
    if not email:
        raise HTTPException(404, "Email not found")

    spam_score, spam_label, _ = SpamDetector().score(
        email.subject or "", email.body_text or "",
        email.sender or "", email.recipients or ""
    )
    classifier = EmailClassifier()
    cat_label, cat_conf = classifier.classify(email.subject or "", email.body_text or "", email.body_html or "")
    confidence = compute_confidence(spam_score, cat_conf)
    routing = route_email(spam_label, cat_label, confidence, 0.0)

    pred = PredictionRecord(email_id=email_id, spam_score=spam_score, spam_label=spam_label,
                            category_label=cat_label, category_confidence=confidence,
                            priority_score=0.0, routed_folder=routing["routed_folder"],
                            routed_action=routing["routed_action"])
    PredictionRepository(db).save_prediction(pred)

    return ClassifyResponse(email_id=email_id, spam_score=spam_score, spam_label=spam_label,
                            category_label=cat_label, category_confidence=confidence,
                            priority_score=0.0, **routing)


@router.post("/route/email", response_model=ClassifyResponse)
def route_email_endpoint(email_id: int = Query(...), db: Session = Depends(get_db)):
    return classify_email(email_id, db)


@router.get("/emails", response_model=List[EmailOut])
def list_emails(skip: int = Query(0), limit: int = Query(100), db: Session = Depends(get_db)):
    return EmailRepository(db).list_inbox_emails(skip=skip, limit=limit)


@router.get("/emails/{email_id}", response_model=EmailOut)
def get_email(email_id: int, db: Session = Depends(get_db)):
    email = EmailRepository(db).get_email(email_id)
    if not email:
        raise HTTPException(404, "Email not found")
    return email


@router.post("/feedback", response_model=FeedbackResponse)
def add_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    if not EmailRepository(db).get_email(req.email_id):
        raise HTTPException(404, "Email not found")
    capture_feedback(db, req.email_id, req.old_label, req.corrected_label, req.corrected_by, req.note)
    return FeedbackResponse(feedback_id=req.email_id, status="recorded")


@router.get("/metrics", response_model=MetricsResponse)
def metrics(db: Session = Depends(get_db)):
    return MetricsResponse(**get_metrics(db))


@router.get("/activities", response_model=List[ActivityOut])
def list_activities(skip: int = Query(0), limit: int = Query(50), db: Session = Depends(get_db)):
    logs = AuditLogRepository(db).list_logs(skip=skip, limit=limit)
    return logs


@router.post("/retrain", response_model=RetrainResponse)
def retrain(db: Session = Depends(get_db)):
    AuditLogRepository(db).log(email_id=None, event_type="retrain_triggered", payload=None)
    return RetrainResponse(status="ok", message="SLM does not require retraining")


@router.post("/cleanup/spam", response_model=CleanupResponse)
def cleanup():
    moved = move_spam_to_trash()
    deleted = cleanup_trash_all()
    return CleanupResponse(status="ok", moved_count=moved, deleted_count=deleted)


@router.delete("/emails/{email_id}")
def delete_email(email_id: int, db: Session = Depends(get_db)):
    repo = EmailRepository(db)
    audit = AuditLogRepository(db)
    email = repo.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    repo.move_to_trash(email_id)
    audit.log(email_id=email.id, event_type="email_moved_to_trash",
              payload={"message_id": email.message_id, "subject": email.subject})
    return {"status": "moved_to_trash"}



