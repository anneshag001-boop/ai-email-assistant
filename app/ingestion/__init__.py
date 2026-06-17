from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class NormalizedEmail:
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
    language: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "message_id": self.message_id,
            "sender": self.sender,
            "recipients": self.recipients,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "thread_id": self.thread_id,
            "attachments_count": self.attachments_count,
            "language": self.language,
        }
