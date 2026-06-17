#!/usr/bin/env python
import logging
from app.storage.db import init_db, SessionLocal
from app.storage.repository import AuditLogRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed():
    init_db()
    db = SessionLocal()
    try:
        AuditLogRepository(db).log(email_id=None, event_type="system_init",
                                    payload={"action": "database_initialized"})
        logger.info("Database initialized")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
