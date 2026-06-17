from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IngestEmailRequest(BaseModel):
    provider: str
    message_id: str
    sender: str
    recipients: Optional[str] = None
    subject: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    received_at: Optional[datetime] = None
    thread_id: Optional[str] = None
    attachments_count: int = 0


class IngestEmailResponse(BaseModel):
    email_id: int
    message_id: str
    status: str


class ClassifyResponse(BaseModel):
    email_id: int
    spam_score: float
    spam_label: str
    category_label: str
    category_confidence: float
    priority_score: float
    routed_folder: str
    routed_action: str


class FeedbackRequest(BaseModel):
    email_id: int
    old_label: str
    corrected_label: str
    corrected_by: Optional[str] = "user"
    note: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: int
    status: str


class ComposeRequest(BaseModel):
    to: str
    subject: str = ""
    body: str = ""


class ReplyRequest(BaseModel):
    body: str


class ComposeResponse(BaseModel):
    email_id: int
    status: str


class EmailOut(BaseModel):
    id: int
    provider: str
    message_id: str
    sender: str
    recipients: Optional[str] = None
    subject: Optional[str] = None
    body_text: Optional[str] = None
    received_at: Optional[datetime] = None
    thread_id: Optional[str] = None
    attachments_count: int = 0
    is_sent: bool = False
    in_reply_to_id: Optional[int] = None

    class Config:
        from_attributes = True


class AccountIn(BaseModel):
    email: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    imap_user: Optional[str] = None
    imap_password: Optional[str] = None
    imap_use_ssl: bool = True
    is_default: bool = False


class AccountOut(BaseModel):
    id: int
    email: str
    smtp_host: str
    smtp_port: int
    smtp_user: Optional[str] = None
    smtp_use_tls: bool
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    imap_user: Optional[str] = None
    imap_use_ssl: bool = True
    has_imap_password: bool = False
    gmail_connected: bool = False
    is_default: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MetricsResponse(BaseModel):
    total_emails: int
    total_predictions: int
    total_feedback: int
    spam_count: int
    folder_distribution: dict
    correction_rate_pct: float
    spam_rate_pct: float
    false_positive_rate_pct: float


class ContainerOut(BaseModel):
    id: int
    name: str
    is_default: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContainerIn(BaseModel):
    name: str


class RetrainResponse(BaseModel):
    status: str
    message: str


class CleanupResponse(BaseModel):
    status: str
    moved_count: int = 0
    deleted_count: int = 0


class ActivityOut(BaseModel):
    id: int
    email_id: Optional[int] = None
    event_type: str
    event_payload: Optional[dict] = None
    created_at: datetime
