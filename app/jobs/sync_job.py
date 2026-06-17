import logging
import base64
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
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


def process_email(email: NormalizedEmail, db: Session, client: IMAPClient):
    email_repo = EmailRepository(db)
    pred_repo = PredictionRepository(db)
    audit = AuditLogRepository(db)

    if is_duplicate_in_db(email, email_repo):
        return False

    email = parse_email(email)
    cleaned = clean_body(email.body_text, email.body_html)

    saved = email_repo.save_email(EmailRecord(
        provider=email.provider, message_id=email.message_id,
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
        email_id=saved.id, spam_score=spam_score, spam_label=spam_label,
        category_label=cat_label, category_confidence=confidence,
        priority_score=0.0, routed_folder=target_folder,
        routed_action=action,
    ))

    audit.log(email_id=saved.id, event_type="email_processed",
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


def sync_imap(host: str, port: int, username: str, password: str, use_ssl: bool = True, fetch_all: bool = False):
    client = IMAPClient(host, port, username, password, use_ssl)
    count = 0
    try:
        client.connect()
        db = SessionLocal()
        try:
            emails = client.fetch_all() if fetch_all else client.fetch_unseen()
            for email in emails:
                if process_email(email, db, client):
                    count += 1
        finally:
            db.close()
    finally:
        client.disconnect()
    return count


def sync_gmail_oauth(account_id: int) -> dict:
    db = SessionLocal()
    try:
        repo = AccountRepository(db)
        account = repo.get_account(account_id)
        if not account:
            return {"status": "error", "message": "Account not found"}
        token_data = repo.get_gmail_token(account_id)
        if not token_data:
            return {"status": "error", "message": "Gmail not connected. Authorize first."}

        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token_data.get("client_id", ""),
            client_secret=token_data.get("client_secret", ""),
            expiry=datetime.fromisoformat(token_data["expiry"]) if token_data.get("expiry") else None,
        )

        from google.auth.transport.requests import Request
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", q="is:unseen", maxResults=50).execute()
        emails = []
        for msg_meta in results.get("messages", []):
            try:
                msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
                headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
                received_at = None
                try:
                    if headers.get("date"):
                        received_at = datetime.strptime(headers["date"], "%a, %d %b %Y %H:%M:%S %z")
                except ValueError:
                    pass
                body_text, body_html, attachments_count = _extract_gmail_parts(msg["payload"])
                normalized = NormalizedEmail(
                    provider="gmail", message_id=headers.get("message-id", msg["id"]),
                    sender=headers.get("from", ""), recipients=headers.get("to", ""),
                    subject=headers.get("subject", ""),
                    body_text=body_text or msg.get("snippet", ""),
                    body_html=body_html, received_at=received_at,
                    thread_id=msg.get("threadId", ""),
                    attachments_count=attachments_count,
                )
                emails.append(normalized)
            except Exception as e:
                logger.warning("Failed to fetch Gmail msg %s: %s", msg_meta["id"], e)

        count = 0
        for email in emails:
            from app.preprocessing.cleaner import clean_body
            from app.preprocessing.parser import parse_email
            from app.preprocessing.dedupe import is_duplicate_in_db

            email_repo = EmailRepository(db)
            if is_duplicate_in_db(email, email_repo):
                continue
            email = parse_email(email)
            cleaned = clean_body(email.body_text, email.body_html)
            saved = email_repo.save_email(EmailRecord(
                provider="gmail", message_id=email.message_id,
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
            PredictionRepository(db).save_prediction(PredictionRecord(
                email_id=saved.id, spam_score=spam_score, spam_label=spam_label,
                category_label=cat_label, category_confidence=confidence,
                priority_score=0.0, routed_folder=routing["routed_folder"],
                routed_action=routing["routed_action"],
            ))
            AuditLogRepository(db).log(email_id=saved.id, event_type="email_processed",
                payload={"spam": spam_label, "category": cat_label, "folder": routing["routed_folder"]})
            count += 1

        return {"status": "ok", "synced": count}
    except Exception as e:
        logger.error("sync_gmail_oauth(%d) failed: %s", account_id, str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def _extract_gmail_parts(payload: dict):
    import base64
    mime_type = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data", "")
    body_text = body_html = ""
    attachments_count = 1 if payload.get("filename") else 0
    if mime_type == "text/plain" and data:
        body_text += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    elif mime_type == "text/html" and data:
        body_html += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    for part in payload.get("parts", []):
        bt, bh, ac = _extract_gmail_parts(part)
        body_text += bt
        body_html += bh
        attachments_count += ac
    return body_text, body_html, attachments_count


def sync_account(account_id: int) -> dict:
    db = SessionLocal()
    try:
        repo = AccountRepository(db)
        account = repo.get_account(account_id)
        if not account:
            return {"status": "error", "message": "Account not found"}
        if not account.imap_host or not account.imap_password:
            return {"status": "error", "message": "IMAP not configured for this account"}

        password = repo.decrypt_password(account.imap_password)
        imap_user = account.imap_user or account.email

        count = sync_imap(
            host=account.imap_host,
            port=account.imap_port,
            username=imap_user,
            password=password,
            use_ssl=account.imap_use_ssl,
            fetch_all=False,
        )
        return {"status": "ok", "synced": count}
    except Exception as e:
        logger.error("sync_account(%d) failed: %s", account_id, str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
