import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey, Boolean, Index
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EmailRecord(Base):
    __tablename__ = "email_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    message_id = Column(String(255), nullable=False)
    sender = Column(String(255), nullable=False)
    recipients = Column(Text, nullable=True)
    subject = Column(String(512), nullable=True)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=True, index=True)
    thread_id = Column(String(255), nullable=True)
    attachments_count = Column(Integer, default=0)
    language = Column(String(10), nullable=True)
    ingested_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_sent = Column(Boolean, default=False)
    in_reply_to_id = Column(Integer, ForeignKey("email_records.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        Index("ix_email_record_dedup", "message_id", "provider", "user_id"),
    )


class PredictionRecord(Base):
    __tablename__ = "prediction_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email_id = Column(Integer, ForeignKey("email_records.id"), nullable=False, index=True)
    spam_score = Column(Float, default=0.0)
    spam_label = Column(String(20), nullable=True)
    category_label = Column(String(50), nullable=True)
    category_confidence = Column(Float, default=0.0)
    priority_score = Column(Float, default=0.0)
    routed_folder = Column(String(50), nullable=True)
    routed_action = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class FeedbackRecord(Base):
    __tablename__ = "feedback_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email_id = Column(Integer, ForeignKey("email_records.id"), nullable=False)
    old_label = Column(String(50), nullable=True)
    corrected_label = Column(String(50), nullable=False)
    corrected_by = Column(String(255), nullable=True)
    corrected_at = Column(DateTime, default=datetime.datetime.utcnow)
    note = Column(Text, nullable=True)


class Container(Base):
    __tablename__ = "containers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EmailAccount(Base):
    __tablename__ = "email_accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    smtp_host = Column(String(255), default="smtp.gmail.com")
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_use_tls = Column(Boolean, default=True)
    imap_host = Column(String(255), default="imap.gmail.com")
    imap_port = Column(Integer, default=993)
    imap_user = Column(String(255), nullable=True)
    imap_password = Column(String(255), nullable=True)
    imap_use_ssl = Column(Boolean, default=True)
    gmail_token = Column(Text, nullable=True)
    gmail_token_expiry = Column(DateTime, nullable=True)
    is_default = Column(Boolean, default=False)
    initial_sync_done = Column(Boolean, default=False)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    email_id = Column(Integer, ForeignKey("email_records.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    event_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
