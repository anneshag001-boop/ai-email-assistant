from typing import List, Optional
import requests
import logging
from datetime import datetime
from app.ingestion import NormalizedEmail

logger = logging.getLogger(__name__)
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


class OutlookClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })

    def fetch_unseen(self) -> List[NormalizedEmail]:
        url = f"{GRAPH_API_BASE}/me/messages?$filter=isRead eq false&$top=50"
        resp = self.session.get(url)
        resp.raise_for_status()
        emails = []
        for msg in resp.json().get("value", []):
            try:
                emails.append(self._parse_message(msg))
            except Exception as e:
                logger.warning("Failed to parse Outlook message: %s", e)
        return emails

    def _parse_message(self, msg: dict) -> Optional[NormalizedEmail]:
        received_at = None
        if msg.get("receivedDateTime"):
            received_at = datetime.fromisoformat(msg["receivedDateTime"].replace("Z", "+00:00"))

        body = msg.get("body", {})
        body_html = body.get("content", "") if body.get("contentType") == "html" else ""
        body_text = body.get("content", "") if body.get("contentType") == "text" else ""

        return NormalizedEmail(
            provider="outlook", message_id=msg.get("id", ""),
            sender=msg.get("from", {}).get("emailAddress", {}).get("address", ""),
            recipients="; ".join(
                r.get("emailAddress", {}).get("address", "") for r in msg.get("toRecipients", [])
            ),
            subject=msg.get("subject", ""),
            body_text=body_text, body_html=body_html,
            received_at=received_at, thread_id=msg.get("conversationId", ""),
            attachments_count=1 if msg.get("hasAttachments") else 0,
        )

    def move_to_folder(self, message_id: str, folder_id: str):
        self.session.post(f"{GRAPH_API_BASE}/me/messages/{message_id}/move", json={"destinationId": folder_id})

    def trash_message(self, message_id: str):
        self.session.post(f"{GRAPH_API_BASE}/me/messages/{message_id}/move", json={"destinationId": "deleteditems"})
