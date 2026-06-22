from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.storage.models import EmailRecord, PredictionRecord, FeedbackRecord, Container


def get_metrics(db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    base = db.query(func.count(EmailRecord.id))
    if user_id:
        base = base.filter(EmailRecord.user_id == user_id)
    total_emails = base.scalar() or 0

    pbase = db.query(func.count(PredictionRecord.id))
    if user_id:
        pbase = pbase.filter(PredictionRecord.user_id == user_id)
    total_predictions = pbase.scalar() or 0

    fbase = db.query(func.count(FeedbackRecord.id))
    if user_id:
        fbase = fbase.filter(FeedbackRecord.user_id == user_id)
    total_feedback = fbase.scalar() or 0

    sbase = db.query(func.count(PredictionRecord.id)).filter(PredictionRecord.spam_label == "spam")
    if user_id:
        sbase = sbase.filter(PredictionRecord.user_id == user_id)
    spam_count = sbase.scalar() or 0

    folder_counts = {}
    q = db.query(PredictionRecord.routed_folder, func.count(PredictionRecord.id))
    if user_id:
        q = q.filter(PredictionRecord.user_id == user_id)
    for row in q.group_by(PredictionRecord.routed_folder).all():
        folder_counts[row[0]] = row[1]

    folder_distribution = {}
    cq = db.query(Container)
    if user_id:
        cq = cq.filter(Container.user_id == user_id)
    for c in cq.order_by(Container.sort_order).all():
        folder_distribution[c.name] = folder_counts.get(c.name, 0)
    for name, count in folder_counts.items():
        if name and name not in folder_distribution:
            folder_distribution[name] = count

    corr_base = db.query(FeedbackRecord).filter(
        FeedbackRecord.old_label != FeedbackRecord.corrected_label)
    if user_id:
        corr_base = corr_base.filter(FeedbackRecord.user_id == user_id)
    corrections = corr_base.count()

    return {
        "total_emails": total_emails, "total_predictions": total_predictions,
        "total_feedback": total_feedback, "spam_count": spam_count,
        "folder_distribution": folder_distribution,
        "correction_rate_pct": round((total_feedback / max(total_predictions, 1)) * 100, 2),
        "spam_rate_pct": round((spam_count / max(total_predictions, 1)) * 100, 2),
        "false_positive_rate_pct": round((corrections / max(total_feedback, 1)) * 100, 2),
    }
