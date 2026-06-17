"""Seed demo emails into the database so the dashboard shows data.
Run: python scripts\seed_demo_data.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.storage.db import SessionLocal, init_db
from app.storage.models import EmailRecord, PredictionRecord
from app.storage.repository import EmailRepository, PredictionRepository, AuditLogRepository
from app.preprocessing.cleaner import clean_body
from app.ai.classifier import EmailClassifier
from app.ai.spam_detector import SpamDetector
from app.ai.scorer import compute_confidence
from app.routing.router import route_email
from datetime import datetime, timedelta

init_db()

demo_emails = [
    {"provider": "test", "message_id": "demo_b1", "sender": "billing@amazon.com",
     "subject": "Your Amazon Invoice #INV-2024-001", "recipients": "user@gmail.com",
     "body_text": "Dear customer, thank you for your purchase. Your invoice of $49.99 is attached. Payment completed via Visa ending in 1234.", "received_at": datetime.utcnow() - timedelta(hours=2)},

    {"provider": "test", "message_id": "demo_p1", "sender": "sarah.friends@gmail.com",
     "subject": "Birthday party this Saturday!", "recipients": "user@gmail.com",
     "body_text": "Hey! It's my birthday this Saturday and I'm throwing a party at my place. Would love to see you there! Bring snacks :)", "received_at": datetime.utcnow() - timedelta(hours=5)},

    {"provider": "test", "message_id": "demo_w1", "sender": "alerts@hdfcbank.com",
     "subject": "OTP 784392 for HDFC Bank Transaction", "recipients": "user@gmail.com",
     "body_text": "Your one-time password for transaction of Rs. 5,000 at Flipkart is 784392. Valid for 5 minutes. Do not share this OTP with anyone.", "received_at": datetime.utcnow() - timedelta(hours=1)},

    {"provider": "test", "message_id": "demo_o1", "sender": "notification@instagram.com",
     "subject": "john_doe liked your photo", "recipients": "user@gmail.com",
     "body_text": "John Doe liked your photo. See what's happening on Instagram.", "received_at": datetime.utcnow() - timedelta(minutes=30)},

    {"provider": "test", "message_id": "demo_s1", "sender": "winner@lottery-intl.com",
     "subject": "CONGRATULATIONS! You Won $1,000,000", "recipients": "user@gmail.com",
     "body_text": "You are the lucky winner of our international lottery! Click here to claim your prize now. Limited time offer! Act now to avoid disappointment.", "received_at": datetime.utcnow() - timedelta(minutes=15)},

    {"provider": "test", "message_id": "demo_b2", "sender": "offers@myntra.com",
     "subject": "FLAT 50% OFF on latest fashion!", "recipients": "user@gmail.com",
     "body_text": "End of season sale! Get flat 50% off on all branded clothing. Use code FASHION50. Shop now at Myntra.", "received_at": datetime.utcnow() - timedelta(hours=3)},

    {"provider": "test", "message_id": "demo_w2", "sender": "googlealerts-noreply@google.com",
     "subject": "Google Alert - AI Technology", "recipients": "user@gmail.com",
     "body_text": "Google Alert: artificial intelligence. 3 new results about AI Technology. Latest news and updates from around the web.", "received_at": datetime.utcnow() - timedelta(hours=4)},

    {"provider": "test", "message_id": "demo_p2", "sender": "dad@family.com",
     "subject": "Weekend trip planning", "recipients": "user@gmail.com",
     "body_text": "Hi, your mom and I are planning a weekend trip to the mountains. Let us know if you want to join us!", "received_at": datetime.utcnow() - timedelta(days=1)},
]

db = SessionLocal()
email_repo = EmailRepository(db)
pred_repo = PredictionRepository(db)
audit = AuditLogRepository(db)
classifier = EmailClassifier()
spam_detector = SpamDetector()

print("Seeding demo emails...")
for i, data in enumerate(demo_emails, 1):
    existing = email_repo.get_email_by_message_id(data["message_id"], "test")
    if existing:
        print(f"  [{i}/8] Skipping (already exists): {data['subject'][:40]}")
        continue

    saved = email_repo.save_email(EmailRecord(
        provider=data["provider"], message_id=data["message_id"],
        sender=data["sender"], recipients=data["recipients"],
        subject=data["subject"],
        body_text=clean_body(data["body_text"], None),
        received_at=data["received_at"],
    ))

    spam_score, spam_label, _ = spam_detector.score(
        data["subject"], data["body_text"], data["sender"], data["recipients"]
    )
    cat_label, cat_conf = classifier.classify(data["subject"], data["body_text"])
    confidence = compute_confidence(spam_score, cat_conf)
    routing = route_email(spam_label, cat_label, confidence, 0.0)

    pred_repo.save_prediction(PredictionRecord(
        email_id=saved.id, spam_score=spam_score, spam_label=spam_label,
        category_label=cat_label, category_confidence=confidence,
        priority_score=0.0, routed_folder=routing["routed_folder"],
        routed_action=routing["routed_action"],
    ))

    audit.log(email_id=saved.id, event_type="demo_seeded",
              payload={"category": cat_label, "folder": routing["routed_folder"]})

    print(f"  [{i}/8] {data['subject'][:50]:50s} -> {cat_label:12s} -> {routing['routed_folder']}")

db.close()
print("\nDone! Demo emails classified and saved.")
print("Refresh http://localhost:8000/dashboard now.")
