import imaplib
import email
from email.utils import parsedate_to_datetime
from typing import List, Optional
import logging
from app.ingestion import NormalizedEmail

logger = logging.getLogger(__name__)


class IMAPClient:
    def __init__(self, host: str, port: int, username: str, password: str, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.conn: Optional[imaplib.IMAP4] = None

    def connect(self):
        if self.use_ssl:
            self.conn = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            self.conn = imaplib.IMAP4(self.host, self.port)
        self.conn.login(self.username, self.password)
        logger.info("Connected to IMAP %s:%s", self.host, self.port)

    def disconnect(self):
        if self.conn:
            self.conn.logout()
            self.conn = None

    def fetch_emails(self, folder: str = "INBOX", unseen_only: bool = True) -> List[NormalizedEmail]:
        if not self.conn:
            raise RuntimeError("Not connected. Call connect() first.")
        self.conn.select(folder)
        search_criteria = "UNSEEN" if unseen_only else "ALL"
        _, data = self.conn.search(None, search_criteria)
        emails = []
        nums = data[0].split() if data[0] else []
        for num in nums:
            try:
                _, msg_data = self.conn.fetch(num, "(RFC822)")
                raw = msg_data[0][1]
                normalized = self._parse_raw(raw, num.decode())
                if normalized:
                    emails.append(normalized)
            except Exception as e:
                logger.warning("Failed to fetch email %s: %s", num, e)
        return emails

    def fetch_unseen(self, folder: str = "INBOX") -> List[NormalizedEmail]:
        return self.fetch_emails(folder, unseen_only=True)

    def fetch_all(self, folder: str = "INBOX") -> List[NormalizedEmail]:
        return self.fetch_emails(folder, unseen_only=False)

    def _parse_raw(self, raw_bytes: bytes, uid: str) -> Optional[NormalizedEmail]:
        msg = email.message_from_bytes(raw_bytes)
        subject = msg.get("Subject", "")
        sender = msg.get("From", "")
        recipients = msg.get("To", "")
        message_id = msg.get("Message-ID", uid)
        date_str = msg.get("Date", "")
        received_at = parsedate_to_datetime(date_str) if date_str else None
        body_text, body_html, attachments_count = self._extract_body(msg)

        return NormalizedEmail(
            provider="imap", message_id=message_id, sender=sender,
            recipients=recipients, subject=subject,
            body_text=body_text, body_html=body_html,
            received_at=received_at, thread_id=msg.get("References", "") or msg.get("In-Reply-To", ""),
            attachments_count=attachments_count,
        )

    def _extract_body(self, msg) -> tuple:
        body_text = body_html = ""
        attachments_count = 0

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in disposition:
                    attachments_count += 1
                    continue
                try:
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    decoded = payload.decode("utf-8", errors="ignore")
                    if ctype == "text/plain":
                        body_text += decoded
                    elif ctype == "text/html":
                        body_html += decoded
                except Exception:
                    continue
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                decoded = payload.decode("utf-8", errors="ignore")
                if msg.get_content_type() == "text/html":
                    body_html = decoded
                else:
                    body_text = decoded

        return body_text, body_html, attachments_count
