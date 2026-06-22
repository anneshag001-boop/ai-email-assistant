import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.storage.db import SessionLocal
from app.storage.repository import AccountRepository
from app.storage.models import EmailAccount
from app.jobs.sync_job import sync_imap

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def poll_all_accounts():
    db = SessionLocal()
    try:
        accounts = db.query(EmailAccount).filter(
            EmailAccount.imap_password.isnot(None)
        ).all()
        for acc in accounts:
            try:
                repo = AccountRepository(db)
                password = repo.decrypt_password(acc.imap_password)
                imap_user = acc.imap_user or acc.email
                count = sync_imap(
                    host=acc.imap_host, port=acc.imap_port,
                    username=imap_user, password=password,
                    use_ssl=acc.imap_use_ssl, fetch_all=False,
                )
                if count > 0:
                    logger.info("Auto-synced %d emails for account %s", count, acc.email)
            except Exception as e:
                logger.error("Auto-sync failed for account %s: %s", acc.email, e)
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        poll_all_accounts,
        IntervalTrigger(minutes=5),
        id="poll_imap",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("IMAP auto-sync scheduler started (every 5 min)")
