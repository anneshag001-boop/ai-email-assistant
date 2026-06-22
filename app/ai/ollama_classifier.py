import json
import logging
import requests
from typing import Tuple, Optional
from app.core.settings import settings

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are an email classifier. Classify this email into exactly ONE category.

Categories:
- private: Personal emails from friends or family, social invitations, personal messages, greetings
- business: Trading websites, business correspondence, brand promotions, clothes/retail brands, offers, purchases, invoices, receipts, cart reminders, order confirmations, product launches
- other_work: Google Alerts, bank alerts/statements, OTP/password emails, login verification codes, WhatsApp/GPay notifications, important app notifications, security alerts, bill reminders, payment confirmations
- others: Facebook, Instagram, Twitter/X, LinkedIn, YouTube, random social media notifications, casual app notifications, newsletters, general announcements
- spam: Unsolicited bulk emails, scams, phishing attempts, fake prizes, lottery, cryptocurrency scams, suspicious offers, unsolicited advertisements

Email Subject: {subject}
Email Body: {body}

Respond with valid JSON only (no other text): {{"category": "...", "confidence": 0.0-1.0}}
"""


class OllamaClassifier:
    def __init__(self, model: Optional[str] = None, host: Optional[str] = None,
                 port: Optional[int] = None, timeout: Optional[int] = None):
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_host
        self.port = port or settings.ollama_port
        self.timeout = timeout or settings.ollama_timeout
        self._base_url = f"http://{self.host}:{self.port}"

    def classify(self, subject: str, body_text: str, body_html: str = None) -> Tuple[str, float]:
        prompt = CLASSIFICATION_PROMPT.format(
            subject=subject or "(no subject)",
            body=(body_text or "(no body)")[:2000]
        )

        try:
            resp = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("response", "{}")
            parsed = json.loads(raw)
            category = parsed.get("category", "others")
            confidence = float(parsed.get("confidence", 0.8))

            if category not in ("private", "business", "other_work", "others", "spam"):
                category = "others"
                confidence = 0.6

            confidence = max(0.0, min(1.0, confidence))
            return category, confidence

        except requests.ConnectionError:
            logger.warning("Ollama connection refused at %s", self._base_url)
            raise
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("Ollama response parse error: %s", e)
            raise
        except requests.Timeout:
            logger.warning("Ollama request timed out after %ds", self.timeout)
            raise
        except requests.RequestException as e:
            logger.error("Ollama request failed: %s", e)
            raise

    def check_health(self) -> bool:
        try:
            resp = requests.get(f"{self._base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False
