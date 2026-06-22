import os; os.chdir("D:\\ai-email-assistant")
from datetime import datetime, timedelta
from app.storage.db import get_db
from app.storage.models import EmailRecord, PredictionRecord
from app.storage.repository import ContainerRepository

db = next(get_db())

container_repo = ContainerRepository(db)
containers = {c.name: c.id for c in container_repo.list_all(user_id=1)}

def classify(subject, body):
    text = (subject + " " + body).lower()
    if any(w in text for w in ["lottery","win","congratulations","click here","free money","urgent"]):
        return "Spam"
    if any(w in text for w in ["invoice","meeting","project","client","proposal","contract","quarterly"]):
        return "Business"
    if any(w in text for w in ["hey","dinner","party","weekend","love","miss you","mom","bro"]):
        return "Private"
    if any(w in text for w in ["conference","workshop","newsletter","webinar","application"]):
        return "Other Work"
    return "Others"

emails = [
    {"sender":"sarah@company.com","subject":"Q3 Budget Review - Meeting Tomorrow",
     "body":"Hi team,\n\nJust a reminder about our Q3 budget review meeting tomorrow at 10 AM. Please bring the quarterly reports.\n\nBest,\nSarah",
     "received_at": datetime.utcnow() - timedelta(hours=2)},
    {"sender":"client@acme-corp.com","subject":"Invoice #4512 - Payment Confirmation",
     "body":"Dear Finance,\n\nWe have received your invoice #4512 and payment is being processed.\n\nRegards,\nAcme Corp",
     "received_at": datetime.utcnow() - timedelta(hours=5)},
    {"sender":"project-bot@company.com","subject":"Sprint Review - Project Alpha",
     "body":"The sprint review for Project Alpha has been scheduled for Friday at 2 PM.\n\n- Project Bot",
     "received_at": datetime.utcnow() - timedelta(days=1)},
    {"sender":"legal@company.com","subject":"Updated NDA Agreement for Review",
     "body":"Please find attached the updated NDA agreement. We need signatures by end of week.\n\nLegal Team",
     "received_at": datetime.utcnow() - timedelta(days=2)},
    {"sender":"mom@family.com","subject":"Dinner this Sunday?",
     "body":"Hey honey,\n\nAre you free for dinner this Sunday? I'm making your favorite pasta!\n\nLove,\nMom",
     "received_at": datetime.utcnow() - timedelta(hours=1)},
    {"sender":"bestfriend@gmail.com","subject":"Weekend plans!",
     "body":"Hey! Great news - I got tickets for the show on Saturday! Let me know if you're in.\n\nCheers,\nAlex",
     "received_at": datetime.utcnow() - timedelta(hours=3)},
    {"sender":"conference@techconf.io","subject":"TechConf 2026 - Registration Confirmed",
     "body":"Thank you for registering for TechConf 2026! Your ticket is confirmed.",
     "received_at": datetime.utcnow() - timedelta(days=3)},
    {"sender":"newsletter@devdigest.com","subject":"Dev Digest - This Week in Programming",
     "body":"Top stories: Python 3.13 released, New VS Code features, and more...",
     "received_at": datetime.utcnow() - timedelta(days=4)},
    {"sender":"winner@lottery-intl.com","subject":"YOU WON $1,000,000!!!",
     "body":"Congratulations! You have been selected as the grand prize winner. Click here to claim now!",
     "received_at": datetime.utcnow() - timedelta(hours=6)},
    {"sender":"admin@secure-bank-login.com","subject":"Urgent: Verify Your Account",
     "body":"Your account has been compromised. Click the link below to verify your credentials immediately.",
     "received_at": datetime.utcnow() - timedelta(hours=8)},
    {"sender":"no-reply@amazon.com","subject":"Your Order #ABC123 Has Shipped",
     "body":"Your package is on its way! Track your delivery using the link below.\n\nAmazon Customer Service",
     "received_at": datetime.utcnow() - timedelta(days=5)},
    {"sender":"notifications@linkedin.com","subject":"You have 5 new connection requests",
     "body":"People want to connect with you on LinkedIn.",
     "received_at": datetime.utcnow() - timedelta(days=1)},
    {"sender":"alert@dropbox.com","subject":"Your shared folder was updated",
     "body":"A file was added to the 'Project Assets' shared folder.",
     "received_at": datetime.utcnow() - timedelta(days=2)},
]

for e in emails:
    folder = classify(e["subject"], e["body"])
    container_id = containers.get(folder)
    msg_id = f"demo-{e['sender'].split('@')[0]}-{int(e['received_at'].timestamp())}"
    record = EmailRecord(
        user_id=1, provider="gmail", message_id=msg_id,
        sender=e["sender"], recipients="me@gmail.com",
        subject=e["subject"], body_text=e["body"],
        received_at=e["received_at"], ingested_at=datetime.utcnow(),
    )
    db.add(record)
    db.flush()
    pred = PredictionRecord(
        user_id=1, email_id=record.id, spam_score=0.0,
        category_label=folder, category_confidence=0.9,
        priority_score=0.0, routed_folder=folder,
    )
    db.add(pred)

# Sent emails
sent = [
    ("sarah@company.com","Re: Q3 Budget Review","Thanks Sarah, I'll be there prepared."),
    ("client@acme-corp.com","Invoice #4512 - Follow Up","Following up on payment status."),
    ("bestfriend@gmail.com","Re: Weekend plans!","Count me in! What time?"),
]
for to, subj, body in sent:
    msg_id = f"sent-demo-{int(datetime.utcnow().timestamp())}-{to.split('@')[0]}"
    record = EmailRecord(
        user_id=1, provider="gmail", message_id=msg_id,
        sender="hrithik@gmail.com", recipients=to,
        subject=subj, body_text=body,
        received_at=datetime.utcnow(), ingested_at=datetime.utcnow(),
        is_sent=True,
    )
    db.add(record)
    db.flush()
    pred = PredictionRecord(
        user_id=1, email_id=record.id, spam_score=0.0,
        category_label="sent", category_confidence=1.0,
        priority_score=0.0, routed_folder="Sent",
    )
    db.add(pred)

db.commit()
db.close()
print(f"Added {len(emails)} inbox + {len(sent)} sent emails with prediction records")
