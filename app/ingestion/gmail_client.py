import pickle
import os
from typing import List, Optional, Tuple
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime
from email.header import decode_header
import base64
import logging
from app.ingestion import NormalizedEmail

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailClient:
    def __init__(self, token_path: str = None,
                 credentials_path: str = None):
        from app.core.settings import settings
        self.token_path = token_path or settings.gmail_token_path
        self.credentials_path = credentials_path or settings.gmail_credentials_path
        self.service = None

    def authenticate(self):
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as f:
                creds = pickle.load(f)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "wb") as f:
                pickle.dump(creds, f)
        self.service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail authenticated")

    def fetch_unseen(self) -> List[NormalizedEmail]:
        if not self.service:
            raise RuntimeError("Not authenticated.")
        results = self.service.users().messages().list(userId="me", q="is:unseen", maxResults=50).execute()
        emails = []
        for msg_meta in results.get("messages", []):
            try:
                msg = self.service.users().messages().get(userId="me", id=msg_meta["id"], format="full").execute()
                normalized = self._parse_message(msg)
                if normalized:
                    emails.append(normalized)
            except Exception as e:
                logger.warning("Failed to fetch Gmail msg %s: %s", msg_meta["id"], e)
        return emails

    @staticmethod
    def _decode_subject(raw: str) -> str:
        if not raw or not raw.startswith("=?"):
            return raw
        try:
            parts = decode_header(raw)
            decoded = []
            for part, charset in parts:
                if isinstance(part, bytes):
                    decoded.append(part.decode(charset or "utf-8", errors="replace"))
                else:
                    decoded.append(str(part))
            return " ".join(decoded)
        except Exception:
            return raw

    def _parse_message(self, msg: dict) -> Optional[NormalizedEmail]:
        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        received_at = None
        try:
            if headers.get("date"):
                received_at = datetime.strptime(headers["date"], "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            pass

        body_text, body_html, attachments_count = self._extract_parts(msg["payload"])

        return NormalizedEmail(
            provider="gmail", message_id=headers.get("message-id", msg["id"]),
            sender=headers.get("from", ""), recipients=headers.get("to", ""),
            subject=self._decode_subject(headers.get("subject", "")),
            body_text=body_text or msg.get("snippet", ""),
            body_html=body_html, received_at=received_at,
            thread_id=msg.get("threadId", ""),
            attachments_count=attachments_count,
        )

    def _extract_parts(self, payload: dict) -> Tuple[str, str, int]:
        mime_type = payload.get("mimeType", "")
        data = payload.get("body", {}).get("data", "")
        body_text = body_html = ""
        attachments_count = 1 if payload.get("filename") else 0

        if mime_type == "text/plain" and data:
            body_text += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        elif mime_type == "text/html" and data:
            body_html += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        for part in payload.get("parts", []):
            bt, bh, ac = self._extract_parts(part)
            body_text += bt
            body_html += bh
            attachments_count += ac

        return body_text, body_html, attachments_count

    def move_to_label(self, message_id: str, label: str):
        self.service.users().messages().modify(
            userId="me", id=message_id,
            body={"addLabelIds": [label], "removeLabelIds": []}
        ).execute()

    def trash_message(self, message_id: str):
        self.service.users().messages().trash(userId="me", id=message_id).execute()
