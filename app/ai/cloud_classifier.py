import json
import logging
from typing import Tuple, Optional
from groq import Groq
from sqlalchemy.orm import Session
from app.core.settings import settings
from app.storage.repository import FeedbackRepository

logger = logging.getLogger(__name__)

GROQ_MODELS = {
    "llama3-8b": "llama3-8b-8192",
    "llama3-70b": "llama3-70b-8192",
    "mixtral": "mixtral-8x7b-32768",
    "gemma2": "gemma2-9b-it",
}

FEW_SHOT_EXAMPLE = """
Here are recent corrections you learned from (old_label -> corrected_label):
{examples}

Learn from these corrections and apply similar logic going forward."""

CLASSIFICATION_PROMPT = """You are an email classifier. Classify this email into exactly ONE category.

Categories:
- private: Personal emails from friends or family, social invitations, personal messages, greetings
- business: Trading websites, business correspondence, brand promotions, purchases, invoices, receipts, order confirmations
- other_work: Google Alerts, bank alerts/statements, OTP/password emails, login verification codes, security alerts, bill reminders
- others: Facebook, Instagram, Twitter/X, LinkedIn, YouTube, newsletters, social media notifications, general announcements
- spam: Unsolicited bulk emails, scams, phishing attempts, fake prizes, lottery, cryptocurrency scams, suspicious offers
{corrections}
Email Subject: {subject}
Email Body: {body}

Respond with valid JSON only (no other text): {{"category": "...", "confidence": 0.0-1.0}}
"""


class CloudClassifier:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None
        self.model = GROQ_MODELS.get(settings.groq_model, "llama3-8b-8192")

    def classify(self, subject: str, body_text: str, body_html: str = None,
                 user_id: Optional[int] = None, db: Optional[Session] = None) -> Tuple[str, float]:
        if not self.client:
            logger.warning("Groq API key not configured, using rule fallback")
            return self._rule_fallback(subject or "", body_text or "")
        corrections_text = ""
        if user_id is not None and db is not None:
            try:
                recent = FeedbackRepository(db).get_recent_corrections(user_id, limit=5)
                if recent:
                    lines = "\n".join(
                        f"  - \"{c['subject']}\" was {c['old_label']} -> {c['corrected_label']}"
                        for c in recent
                    )
                    corrections_text = FEW_SHOT_EXAMPLE.format(examples=lines)
            except Exception as e:
                logger.debug("Failed to fetch corrections for few-shot: %s", e)
        prompt = CLASSIFICATION_PROMPT.format(
            subject=(subject or "(no subject)")[:500],
            body=(body_text or "(no body)")[:2000],
            corrections=corrections_text,
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=100,
            )
            raw = response.choices[0].message.content
            parsed = json.loads(raw)
            category = parsed.get("category", "others")
            confidence = float(parsed.get("confidence", 0.8))
            if category not in ("private", "business", "other_work", "others", "spam"):
                category = "others"
                confidence = 0.6
            return category, max(0.0, min(1.0, confidence))
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._rule_fallback(subject or "", body_text or "")

    def check_health(self) -> bool:
        return bool(settings.groq_api_key)

    def _rule_fallback(self, subject: str, body_text: str) -> Tuple[str, float]:
        text = (subject + " " + body_text).lower()
        if any(w in text for w in ["unsubscribe", "newsletter", "promotion", "sale", "offer"]):
            return "others", 0.7
        if any(w in text for w in ["invoice", "order", "receipt", "purchase", "shipping"]):
            return "business", 0.7
        if any(w in text for w in ["otp", "password", "alert", "verification", "bank"]):
            return "other_work", 0.7
        return "others", 0.5
