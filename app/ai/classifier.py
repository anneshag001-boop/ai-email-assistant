import logging
from typing import Tuple, Optional
from app.ai.ollama_classifier import OllamaClassifier
from app.preprocessing.cleaner import clean_body
from app.core.settings import settings

logger = logging.getLogger(__name__)

FALLBACK_RULES = {
    "private": ["family", "personal", "photo", "party", "invitation", "thank you",
                "love", "mom", "dad", "friend", "birthday", "dinner"],
    "business": ["invoice", "meeting", "project", "proposal", "client", "quote",
                 "purchase order", "contract", "payment", "receipt", "order",
                 "promotion", "sale", "discount", "brand"],
    "other_work": ["alert", "otp", "password", "verification", "login", "bank",
                   "statement", "bill", "security", "notification", "authenticator",
                   "google alert", "2fa", "two-factor"],
    "others": ["facebook", "instagram", "twitter", "linkedin", "youtube",
               "newsletter", "notification", "subscription", "weekly digest"],
}


class EmailClassifier:
    _cached_ollama = None

    def __init__(self):
        if EmailClassifier._cached_ollama is None:
            EmailClassifier._cached_ollama = OllamaClassifier()
        self.ollama = EmailClassifier._cached_ollama

    def classify(self, subject: str, body_text: str, body_html: str = None) -> Tuple[str, float]:
        text = clean_body(body_text, body_html)
        input_text = f"{subject or ''} {text}"

        if not settings.ollama_enabled:
            return self._rule_fallback(subject or "", text)

        try:
            if not self.ollama.check_health():
                logger.warning("Ollama not reachable, using fallback rules")
                return self._rule_fallback(subject or "", text)
            return self.ollama.classify(subject or "", text)
        except Exception as e:
            logger.warning("Ollama classification failed (%s), using fallback rules", e)
            return self._rule_fallback(subject or "", text)

    def _rule_fallback(self, subject: str, body: str) -> Tuple[str, float]:
        lower = f"{subject} {body}".lower()
        scores = {}
        for cat, kws in FALLBACK_RULES.items():
            scores[cat] = sum(1 for kw in kws if kw in lower) / max(len(kws), 1)

        best = max(scores, key=scores.get)
        confidence = scores[best]

        if confidence == 0:
            return "others", 0.65

        boosted = min((confidence * 2) + 0.60, 0.99)
        return best, boosted

    @classmethod
    def reset_cache(cls):
        cls._cached_ollama = None
