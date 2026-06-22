import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.storage.repository import FeedbackRepository, AuditLogRepository
from app.storage.models import FeedbackRecord


def capture_feedback(db: Session, email_id: int, old_label: str, corrected_label: str,
                     corrected_by: Optional[str] = None, note: Optional[str] = None,
                     user_id: Optional[int] = None) -> FeedbackRecord:
    fb_repo = FeedbackRepository(db)
    audit = AuditLogRepository(db)

    fb = FeedbackRecord(
        user_id=user_id or 1, email_id=email_id, old_label=old_label,
        corrected_label=corrected_label, corrected_by=corrected_by or "user",
        corrected_at=datetime.datetime.utcnow(), note=note,
    )
    saved = fb_repo.save_feedback(fb)
    audit.log(email_id=email_id, user_id=user_id, event_type="feedback_captured",
              payload={"old_label": old_label, "corrected_label": corrected_label})
    return saved
