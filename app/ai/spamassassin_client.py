import socket
import logging
from typing import Tuple, Optional
from app.core.settings import settings

logger = logging.getLogger(__name__)


class SpamAssassinClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 783, timeout: int = 30):
        self.host = host or settings.spamassassin_host
        self.port = port or settings.spamassassin_port
        self.timeout = timeout

    def score(self, subject: str, body: str, sender: str = "",
              recipients: str = "") -> Tuple[float, str, dict]:
        try:
            report = self._check_spamd(subject, body, sender, recipients)
            score = report.get("score", 0.0)
            threshold = settings.spam_threshold
            label = "spam" if score >= threshold else "not_spam"
            return score, label, report
        except ConnectionRefusedError:
            logger.warning("SpamAssassin not available, falling back")
            return 0.0, "not_spam", {}
        except Exception as e:
            logger.error("SpamAssassin error: %s", e)
            return 0.0, "not_spam", {}

    def _check_spamd(self, subject: str, body: str, sender: str,
                     recipients: str) -> dict:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.host, self.port))
            payload = (
                f"Subject: {subject}\r\n"
                f"From: {sender}\r\n"
                f"To: {recipients}\r\n"
                f"\r\n"
                f"{body}"
            )
            protocol_req = (
                f"SYMBOLS SPAMC/1.5\r\n"
                f"Content-Length: {len(payload.encode('utf-8'))}\r\n"
                f"User: ai-email-assistant\r\n"
                f"\r\n"
                f"{payload}"
            )
            sock.sendall(protocol_req.encode("utf-8"))
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if b"\r\n\r\n" in response and len(response) > 1000:
                    break
            return self._parse_response(response.decode("utf-8", errors="ignore"))
        finally:
            sock.close()

    def _parse_response(self, raw: str) -> dict:
        result = {"score": 0.0, "symbols": [], "report": raw}
        for line in raw.split("\r\n"):
            if line.startswith("Spam:"):
                parts = line.split("/")
                try:
                    result["score"] = float(parts[0].split()[-1])
                except (ValueError, IndexError):
                    pass
            elif line.strip() and not line.startswith("SPAMD") and not line.startswith("Content"):
                result["symbols"].append(line.strip())
        return result
