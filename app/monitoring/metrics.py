from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.storage.models import EmailRecord, PredictionRecord, FeedbackRecord, Container


def get_metrics(db: Session) -> Dict[str, Any]:
    total_emails = db.query(func.count(EmailRecord.id)).scalar() or 0
    total_predictions = db.query(func.count(PredictionRecord.id)).scalar() or 0
    total_feedback = db.query(func.count(FeedbackRecord.id)).scalar() or 0
    spam_count = db.query(func.count(PredictionRecord.id)).filter(
        PredictionRecord.spam_label == "spam").scalar() or 0

    folder_counts = {}
    for row in db.query(PredictionRecord.routed_folder, func.count(PredictionRecord.id)).group_by(
            PredictionRecord.routed_folder).all():
        folder_counts[row[0]] = row[1]

    # Include all registered containers (even with 0 emails)
    folder_distribution = {}
    for c in db.query(Container).order_by(Container.sort_order).all():
        folder_distribution[c.name] = folder_counts.get(c.name, 0)
    # Also include any unregistered folders from predictions
    for name, count in folder_counts.items():
        if name and name not in folder_distribution:
            folder_distribution[name] = count

    corrections = db.query(FeedbackRecord).filter(
        FeedbackRecord.old_label != FeedbackRecord.corrected_label).count()

    return {
        "total_emails": total_emails, "total_predictions": total_predictions,
        "total_feedback": total_feedback, "spam_count": spam_count,
        "folder_distribution": folder_distribution,
        "correction_rate_pct": round((total_feedback / max(total_predictions, 1)) * 100, 2),
        "spam_rate_pct": round((spam_count / max(total_predictions, 1)) * 100, 2),
        "false_positive_rate_pct": round((corrections / max(total_feedback, 1)) * 100, 2),
    }
