import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.ingestion import NormalizedEmail
from app.ingestion.imap_client import IMAPClient
from app.preprocessing.cleaner import clean_body
from app.preprocessing.parser import parse_email
from app.preprocessing.dedupe import is_duplicate_in_db
from app.storage.repository import EmailRepository, PredictionRepository, AuditLogRepository, AccountRepository
from app.storage.models import EmailRecord, PredictionRecord
from app.storage.db import SessionLocal
from app.ai.spam_detector import SpamDetector
from app.ai.classifier import EmailClassifier
from app.ai.scorer import compute_confidence
from app.routing.router import route_email

logger = logging.getLogger(__name__)


def process_email(email: NormalizedEmail, db: Session, client: IMAPClient, user_id: int = 1):
    email_repo = EmailRepository(db)
    pred_repo = PredictionRepository(db)
    audit = AuditLogRepository(db)

    if is_duplicate_in_db(email, email_repo, user_id=user_id):
        return False

    email = parse_email(email)
    cleaned = clean_body(email.body_text, email.body_html)

    saved = email_repo.save_email(EmailRecord(
        user_id=user_id, provider=email.provider, message_id=email.message_id,
        sender=email.sender, recipients=email.recipients,
        subject=email.subject, body_text=cleaned, body_html=email.body_html,
        received_at=email.received_at, thread_id=email.thread_id,
        attachments_count=email.attachments_count,
    ))

    spam_score, spam_label, _ = SpamDetector().score(
        email.subject or "", cleaned, email.sender or "", email.recipients or ""
    )
    classifier = EmailClassifier()
    cat_label, cat_conf = classifier.classify(email.subject or "", cleaned)
    confidence = compute_confidence(spam_score, cat_conf)
    routing = route_email(spam_label, cat_label, confidence, 0.0)
    target_folder = routing["routed_folder"]
    action = routing["routed_action"]

    pred_repo.save_prediction(PredictionRecord(
        user_id=user_id, email_id=saved.id, spam_score=spam_score, spam_label=spam_label,
        category_label=cat_label, category_confidence=confidence,
        priority_score=0.0, routed_folder=target_folder,
        routed_action=action,
    ))

    audit.log(email_id=saved.id, user_id=user_id, event_type="email_processed",
              payload={"spam": spam_label, "category": cat_label, "folder": target_folder})

    try:
        if action == "move_to_folder" and hasattr(client, 'move_to_folder'):
            client.move_to_folder(email.message_id, target_folder)
            logger.info("Moved %s to [%s]", email.message_id, target_folder)
        elif action == "archive" and hasattr(client, 'move_to_folder'):
            client.move_to_folder(email.message_id, "Archive")
            logger.info("Archived %s", email.message_id)
        elif action == "delete_after_30_days" and hasattr(client, 'move_to_folder'):
            client.move_to_folder(email.message_id, "Spam")
            logger.info("Trashed spam %s", email.message_id)
    except Exception as e:
        logger.error("Failed to move email autonomously: %s", str(e))

    return True


def sync_imap(host: str, port: int, username: str, password: str, use_ssl: bool = True, fetch_all: bool = False, user_id: int = 1):
    client = IMAPClient(host, port, username, password, use_ssl)
    count = 0
    try:
        client.connect()
        db = SessionLocal()
        try:
            emails = client.fetch_all() if fetch_all else client.fetch_unseen()
            for email in emails:
                if process_email(email, db, client, user_id=user_id):
                    count += 1
        finally:
            db.close()
    finally:
        client.disconnect()
    return count


def sync_account(account_id: int) -> dict:
    db = SessionLocal()
    try:
        repo = AccountRepository(db)
        account = repo.get_account(account_id)
        if not account:
            return {"status": "error", "message": "Account not found"}
        if not account.imap_host or not account.imap_password:
            return {"status": "error", "message": "IMAP not configured for this account"}
        user_id = account.user_id or 1
        password = repo.decrypt_password(account.imap_password)
        imap_user = account.imap_user or account.email

        count = sync_imap(
            host=account.imap_host, port=account.imap_port,
            username=imap_user, password=password,
            use_ssl=account.imap_use_ssl, fetch_all=False,
            user_id=user_id,
        )
        return {"status": "ok", "synced": count}
    except Exception as e:
        logger.error("sync_account(%d) failed: %s", account_id, str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
