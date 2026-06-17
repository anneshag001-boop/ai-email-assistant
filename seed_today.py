import os; os.chdir("D:\\ai-email-assistant")
from datetime import datetime, timedelta
from app.storage.db import get_db, engine
from app.storage.models import EmailRecord, PredictionRecord
from sqlalchemy import text

conn = engine.connect()
conn.execute(text("DELETE FROM prediction_records"))
conn.execute(text("DELETE FROM email_records"))
conn.commit()
conn.close()

db = next(get_db())

# Use current time (UTC). The server formats dates via strftime, JS uses browser time.
# To match, use a fixed known-good date or adjust based on server time alignment.
# For now, just use datetime.utcnow() which is what the DB stores.
now = datetime.utcnow()
today_str = now.strftime("%Y-%m-%d")

emails = [
    ("sarah@company.com", "Q3 Budget Review - Meeting Tomorrow",
     "Hi team,\n\nReminder about Q3 budget review tomorrow at 10 AM.\n\nBest,\nSarah",
     now - timedelta(hours=1), "Business"),
    ("client@acme-corp.com", "Invoice #4512 - Payment Confirmation",
     "Invoice #4512 payment is being processed.\n\nRegards,\nAcme Corp",
     now - timedelta(hours=3), "Business"),
    ("mom@family.com", "Dinner this Sunday?",
     "Hey honey,\n\nFree for dinner Sunday? Making pasta!\n\nLove,\nMom",
     now - timedelta(minutes=30), "Private"),
    ("bestfriend@gmail.com", "Weekend plans!",
     "Got tickets for Saturday! Let me know.\n\nAlex",
     now - timedelta(hours=2), "Private"),
    ("conference@techconf.io", "TechConf 2026 - Registration Confirmed",
     "Your ticket is confirmed. Schedule next week.",
     now - timedelta(hours=6), "Other Work"),
    ("newsletter@devdigest.com", "Dev Digest - This Week in Programming",
     "Python 3.13 released, VS Code updates and more.",
     now - timedelta(hours=8), "Other Work"),
    ("winner@lottery-intl.com", "YOU WON $1,000,000!!!",
     "Grand prize winner! Click here to claim now!",
     now - timedelta(hours=36), "Spam"),
    ("admin@secure-bank-login.com", "Urgent: Verify Your Account",
     "Account compromised! Verify immediately.",
     now - timedelta(hours=5), "Spam"),
    ("no-reply@amazon.com", "Your Order #ABC123 Has Shipped",
     "Your package is on its way! Track delivery.",
     now - timedelta(hours=7), "Others"),
    ("notifications@linkedin.com", "5 new connection requests",
     "People want to connect with you on LinkedIn.",
     now - timedelta(hours=8), "Others"),
]

for sender, subject, body, received, folder in emails:
    msg_id = f"d-{sender.split('@')[0]}-{int(received.timestamp())}"
    rec = EmailRecord(
        provider="gmail", message_id=msg_id,
        sender=sender, recipients="hrithik@gmail.com",
        subject=subject, body_text=body,
        received_at=received, ingested_at=now,
    )
    db.add(rec)
    db.flush()
    cat_label = folder
    rfolder = folder
    raction = None
    if folder == "Spam":
        cat_label = "spam"
        raction = "move_to_trash_after_1d"
    pred = PredictionRecord(
        email_id=rec.id, spam_score=0.0,
        spam_label="spam" if folder == "Spam" else None,
        category_label=cat_label, category_confidence=0.9,
        priority_score=0.0, routed_folder=rfolder,
        routed_action=raction,
    )
    db.add(pred)

sent = [
    ("sarah@company.com", "Re: Q3 Budget Review", "I'll be there prepared."),
    ("bestfriend@gmail.com", "Re: Weekend plans!", "Count me in! What time?"),
]
for to, subj, body in sent:
    msg_id = f"st-{int(now.timestamp())}-{to.split('@')[0]}"
    rec = EmailRecord(
        provider="gmail", message_id=msg_id,
        sender="hrithik@gmail.com", recipients=to,
        subject=subj, body_text=body,
        received_at=now, ingested_at=now,
        is_sent=True,
    )
    db.add(rec)
    db.flush()
    pred = PredictionRecord(
        email_id=rec.id, spam_score=0.0,
        category_label="sent", category_confidence=1.0,
        priority_score=0.0, routed_folder="Sent",
    )
    db.add(pred)

db.commit()
db.close()
print(f"Seeded {len(emails)} inbox + {len(sent)} sent (UTC date: {today_str})")
