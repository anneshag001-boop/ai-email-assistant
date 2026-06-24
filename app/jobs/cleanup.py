import datetime
import logging
from app.storage.db import SessionLocal
from app.storage.repository import AuditLogRepository
from app.storage.models import EmailRecord, PredictionRecord

logger = logging.getLogger(__name__)


def move_spam_to_trash(user_id: int = None):
    logger.info("Moving spam >1 day old to Trash")
    db = SessionLocal()
    moved = 0
    try:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        q = db.query(EmailRecord).join(
            PredictionRecord, EmailRecord.id == PredictionRecord.email_id
        ).filter(
            PredictionRecord.routed_folder == "Spam",
            EmailRecord.received_at < cutoff,
        )
        if user_id:
            q = q.filter(EmailRecord.user_id == user_id)
        spam_emails = q.all()
        audit = AuditLogRepository(db)
        for email in spam_emails:
            pred = (
                db.query(PredictionRecord)
                .filter(PredictionRecord.email_id == email.id)
                .first()
            )
            if pred:
                pred.routed_folder = "Trash"
                audit.log(email_id=email.id, user_id=email.user_id,
                          event_type="spam_moved_to_trash",
                          payload={"message_id": email.message_id})
                moved += 1
        db.commit()
        logger.info("Moved %d spam emails to Trash", moved)
    except Exception as e:
        db.rollback()
        logger.error("Spam->Trash move failed: %s", e)
    finally:
        db.close()
    return moved


def cleanup_trash_all(user_id: int = None):
    logger.info("Permanently deleting all emails in Trash")
    db = SessionLocal()
    deleted = 0
    try:
        q = db.query(EmailRecord).join(
            PredictionRecord, EmailRecord.id == PredictionRecord.email_id
        ).filter(PredictionRecord.routed_folder == "Trash")
        if user_id:
            q = q.filter(EmailRecord.user_id == user_id)
        trash_emails = q.all()
        audit = AuditLogRepository(db)
        for email in trash_emails:
            audit.log(email_id=email.id, user_id=email.user_id,
                      event_type="trash_cleaned",
                      payload={"message_id": email.message_id})
            db.delete(email)
            deleted += 1
        db.commit()
        logger.info("Permanently deleted %d emails from Trash", deleted)
    except Exception as e:
        db.rollback()
        logger.error("Trash cleanup failed: %s", e)
    finally:
        db.close()
    return deleted


def cleanup_trash_30d():
    logger.info("Auto-deleting Trash emails older than 30 days")
    db = SessionLocal()
    deleted = 0
    try:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        old_trash = (
            db.query(EmailRecord)
            .join(PredictionRecord, EmailRecord.id == PredictionRecord.email_id)
            .filter(PredictionRecord.routed_folder == "Trash")
            .filter(EmailRecord.received_at < cutoff)
            .all()
        )
        audit = AuditLogRepository(db)
        for email in old_trash:
            audit.log(email_id=email.id, user_id=email.user_id,
                      event_type="trash_auto_deleted",
                      payload={"message_id": email.message_id})
            db.delete(email)
            deleted += 1
        db.commit()
        logger.info("Auto-deleted %d Trash emails older than 30 days", deleted)
    except Exception as e:
        db.rollback()
        logger.error("Auto Trash cleanup failed: %s", e)
    finally:
        db.close()
    return deleted


def auto_cleanup():
    moved = move_spam_to_trash()
    deleted = cleanup_trash_30d()
    return moved, deleted
