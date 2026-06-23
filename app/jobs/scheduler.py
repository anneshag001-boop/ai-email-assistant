import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.storage.db import SessionLocal
from app.storage.models import EmailAccount, User
from app.jobs.sync_job import sync_account, classify_unclassified

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

# Lazily import to avoid circular dependency at module level
_connected_clients = None

def _get_clients():
    global _connected_clients
    if _connected_clients is None:
        from app.main import connected_clients as _cls
        _connected_clients = _cls
    return _connected_clients


def poll_all_accounts():
    db = SessionLocal()
    try:
        accounts = db.query(EmailAccount).filter(
            EmailAccount.imap_password.isnot(None)
        ).all()
        for acc in accounts:
            try:
                result = sync_account(acc.id)
                if result.get("status") == "ok" and result.get("synced", 0) > 0:
                    count = result["synced"]
                    logger.info("Auto-synced %d emails for account %s", count, acc.email)
                    _notify_user(acc.user_id, {"type": "new_emails", "count": count, "account": acc.email})
            except Exception as e:
                logger.error("Auto-sync failed for account %s: %s", acc.email, e)
        # Classify any unclassified emails (saved without predictions during initial sync)
        for user in db.query(User).all():
            try:
                classified = classify_unclassified(user.id)
                if classified > 0:
                    logger.info("Classified %d pending emails for user %s", classified, user.email)
            except Exception as e:
                logger.error("Classification failed for user %s: %s", user.email, e)
    finally:
        db.close()


def _notify_user(user_id: int, event: dict):
    import asyncio
    clients = _get_clients()
    for ws in clients.get(user_id, []):
        try:
            asyncio.create_task(ws.send_json(event))
        except Exception:
            pass


def start_scheduler():
    logger.info("Starting IMAP auto-sync scheduler...")
    scheduler.add_job(
        poll_all_accounts,
        IntervalTrigger(seconds=60),
        id="poll_imap",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("IMAP auto-sync scheduler started (every 60s)")
