import datetime
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.storage.models import EmailRecord, PredictionRecord, FeedbackRecord, AuditLog, EmailAccount, Container


class EmailRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_email(self, email: EmailRecord) -> EmailRecord:
        self.db.add(email)
        self.db.commit()
        self.db.refresh(email)
        return email

    def get_email(self, email_id: int) -> Optional[EmailRecord]:
        return self.db.query(EmailRecord).filter(EmailRecord.id == email_id).first()

    def get_email_by_message_id(self, message_id: str, provider: str) -> Optional[EmailRecord]:
        return self.db.query(EmailRecord).filter(
            EmailRecord.message_id == message_id, EmailRecord.provider == provider
        ).first()

    def list_emails(self, skip: int = 0, limit: int = 100) -> List[EmailRecord]:
        return self.db.query(EmailRecord).order_by(desc(EmailRecord.received_at)).offset(skip).limit(limit).all()

    def save_sent_email(self, sender: str, recipients: str, subject: str,
                        body_text: str, in_reply_to_id: Optional[int] = None) -> EmailRecord:
        record = EmailRecord(
            provider="smtp",
            message_id=str(uuid.uuid4()),
            sender=sender,
            recipients=recipients,
            subject=subject,
            body_text=body_text,
            received_at=datetime.datetime.utcnow(),
            is_sent=True,
            in_reply_to_id=in_reply_to_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_sent_emails(self, skip: int = 0, limit: int = 100) -> List[EmailRecord]:
        return self.db.query(EmailRecord).filter(
            EmailRecord.is_sent == True
        ).order_by(desc(EmailRecord.received_at)).offset(skip).limit(limit).all()

    def list_inbox_emails(self, skip: int = 0, limit: int = 100) -> List[EmailRecord]:
        return self.db.query(EmailRecord).filter(
            or_(EmailRecord.is_sent == False, EmailRecord.is_sent.is_(None))
        ).order_by(desc(EmailRecord.received_at)).offset(skip).limit(limit).all()

    def move_to_trash(self, email_id: int) -> bool:
        email = self.db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
        if not email:
            return False
        pred = self.db.query(PredictionRecord).filter(PredictionRecord.email_id == email_id).first()
        if pred:
            pred.routed_folder = "Trash"
        self.db.commit()
        return True

    def save_draft(self, sender: str, recipients: str, subject: str,
                   body_text: str) -> EmailRecord:
        record = EmailRecord(
            provider="smtp",
            message_id=str(uuid.uuid4()),
            sender=sender,
            recipients=recipients,
            subject=subject,
            body_text=body_text,
            received_at=datetime.datetime.utcnow(),
            is_sent=False,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        pred = PredictionRecord(
            email_id=record.id,
            spam_score=0.0,
            spam_label="ham",
            category_label="draft",
            category_confidence=1.0,
            priority_score=0.0,
            routed_folder="Drafts",
            routed_action="none",
        )
        self.db.add(pred)
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete_email(self, email_id: int) -> bool:
        email = self.get_email(email_id)
        if not email:
            return False
        self.db.delete(email)
        self.db.commit()
        return True


class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_prediction(self, pred: PredictionRecord) -> PredictionRecord:
        self.db.add(pred)
        self.db.commit()
        self.db.refresh(pred)
        return pred

    def get_by_email(self, email_id: int) -> Optional[PredictionRecord]:
        return self.db.query(PredictionRecord).filter(PredictionRecord.email_id == email_id).first()

    def list_by_folder(self, folder: str, skip: int = 0, limit: int = 100) -> List[PredictionRecord]:
        return self.db.query(PredictionRecord).filter(
            PredictionRecord.routed_folder == folder
        ).order_by(desc(PredictionRecord.created_at)).offset(skip).limit(limit).all()


class FeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_feedback(self, fb: FeedbackRecord) -> FeedbackRecord:
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb

    def list_all(self, skip: int = 0, limit: int = 100) -> List[FeedbackRecord]:
        return self.db.query(FeedbackRecord).order_by(desc(FeedbackRecord.corrected_at)).offset(skip).limit(limit).all()


DEFAULT_CONTAINERS = ["Private", "Business", "Other Work", "Others", "Spam"]


def seed_default_containers(db: Session):
    existing = db.query(Container).count()
    if existing > 0:
        return
    for i, name in enumerate(DEFAULT_CONTAINERS):
        db.add(Container(name=name, is_default=True, sort_order=i))
    db.commit()


class ContainerRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> List[Container]:
        return self.db.query(Container).order_by(Container.sort_order).all()

    def create(self, name: str) -> Container:
        container = Container(name=name.strip(), is_default=False,
                              sort_order=(self.db.query(Container).count() + 1))
        self.db.add(container)
        self.db.commit()
        self.db.refresh(container)
        return container

    def delete(self, container_id: int) -> bool:
        c = self.db.query(Container).filter(Container.id == container_id).first()
        if not c or c.is_default:
            return False
        self.db.delete(c)
        self.db.commit()
        return True


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_accounts(self) -> List[EmailAccount]:
        return self.db.query(EmailAccount).order_by(EmailAccount.is_default.desc(), EmailAccount.created_at).all()

    def get_account(self, account_id: int) -> Optional[EmailAccount]:
        return self.db.query(EmailAccount).filter(EmailAccount.id == account_id).first()

    def get_default_account(self) -> Optional[EmailAccount]:
        return self.db.query(EmailAccount).filter(EmailAccount.is_default == True).first()

    def get_account_by_email(self, email: str) -> Optional[EmailAccount]:
        return self.db.query(EmailAccount).filter(EmailAccount.email == email).first()

    def create_account(self, email: str, smtp_host: str = "smtp.gmail.com",
                       smtp_port: int = 587, smtp_user: Optional[str] = None,
                       smtp_password: Optional[str] = None, smtp_use_tls: bool = True,
                       imap_host: str = "imap.gmail.com", imap_port: int = 993,
                       imap_user: Optional[str] = None, imap_password: Optional[str] = None,
                       imap_use_ssl: bool = True,
                       is_default: bool = False) -> EmailAccount:
        existing = self.db.query(EmailAccount).count()
        if existing == 0:
            is_default = True
        if is_default:
            self.db.query(EmailAccount).filter(EmailAccount.is_default == True).update({"is_default": False})
        # Encrypt passwords if provided
        smtp_pass_enc = self._encrypt(smtp_password) if smtp_password else None
        imap_pass_enc = self._encrypt(imap_password) if imap_password else None
        account = EmailAccount(
            email=email, smtp_host=smtp_host, smtp_port=smtp_port,
            smtp_user=smtp_user, smtp_password=smtp_pass_enc,
            smtp_use_tls=smtp_use_tls,
            imap_host=imap_host, imap_port=imap_port,
            imap_user=imap_user, imap_password=imap_pass_enc,
            imap_use_ssl=imap_use_ssl,
            is_default=is_default,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        # Clear password fields from object for safety
        account.smtp_password = "[encrypted]" if smtp_pass_enc else None
        account.imap_password = "[encrypted]" if imap_pass_enc else None
        return account

    def delete_account(self, account_id: int) -> bool:
        account = self.db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not account:
            return False
        self.db.delete(account)
        self.db.commit()
        return True

    def set_default(self, account_id: int) -> Optional[EmailAccount]:
        account = self.db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not account:
            return None
        self.db.query(EmailAccount).filter(EmailAccount.is_default == True).update({"is_default": False})
        account.is_default = True
        self.db.commit()
        self.db.refresh(account)
        return account

    def _encrypt(self, value: str) -> str:
        from app.core.auth import encrypt_token
        return encrypt_token(value)

    def decrypt_password(self, encrypted: str) -> str:
        from app.core.auth import decrypt_token
        return decrypt_token(encrypted)

    def set_gmail_token(self, email: str, token_data_json: str) -> bool:
        account = self.db.query(EmailAccount).filter(EmailAccount.email == email).first()
        if not account:
            return False
        from app.core.auth import encrypt_token
        account.gmail_token = encrypt_token(token_data_json)
        account.gmail_token_expiry = datetime.datetime.utcnow()
        self.db.commit()
        return True

    def get_gmail_token(self, account_id: int) -> Optional[dict]:
        account = self.db.query(EmailAccount).filter(EmailAccount.id == account_id).first()
        if not account or not account.gmail_token:
            return None
        from app.core.auth import decrypt_token
        import json
        return json.loads(decrypt_token(account.gmail_token))


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, email_id: Optional[int], event_type: str, payload: Optional[dict] = None) -> AuditLog:
        record = AuditLog(email_id=email_id, event_type=event_type, event_payload=payload)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_logs(self, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        return self.db.query(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
