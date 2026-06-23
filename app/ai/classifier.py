import logging
from email.header import decode_header
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.ai.ollama_classifier import OllamaClassifier
from app.ai.cloud_classifier import CloudClassifier
from app.preprocessing.cleaner import clean_body
from app.core.settings import settings

logger = logging.getLogger(__name__)

FALLBACK_RULES = {
    "private": ["miss you", "miss u", "thinking of you", "hope you",
                "love", "mom", "dad", "brother", "sister", "cousin",
                "uncle", "aunt", "grandma", "grandpa", "friend",
                "how are you", "whats up", "let's catch", "let's meet",
                "happy birthday", "happy anniversary", "congratulations",
                "thank you so much", "sorry", "prayer", "bless",
                "pagli", "pagol", "amr", "bondhu", "bhai", "dada", "didi",
                "call me", "call you", "checking in",
                "dinner", "lunch", "coffee", "weekend", "holiday",
                "how was", "rsvp", "save the date",
                "pictures", "album",
                "home", "school", "college", "university", "class"],
    "business": ["invoice", "receipt", "purchase", "order", "payment",
                 "transaction", "refund", "bill", "quote",
                 "meeting", "project", "proposal", "client", "contract",
                 "conference", "agenda", "follow-up", "deadline",
                 "deliverable", "milestone", "stakeholder", "budget",
                 "profit", "revenue", "forecast",
                 "interview", "hiring", "recruitment", "job offer",
                 "resume", "application", "candidate", "opportunity",
                 "partnership", "collaboration",
                 "shipped", "out for delivery", "order confirmed",
                 "order placed", "your order"],
    "other_work": ["otp", "password", "verification", "login", "sign in",
                   "security code", "verification code", "two-factor",
                   "authenticator", "2fa", "password reset",
                   "alert", "bank", "statement", "account",
                   "confirm your email", "email verified", "welcome to",
                   "automated message", "do not reply", "no-reply",
                   "storage is", "storage", "gmail", "google account", "google play",
                   "privacy settings", "privacy policy", "terms of service",
                   "terms and policies", "annual reminder",
                   "subscription", "renewal", "trial", "expiring",
                   "appointment confirmed", "booking", "reservation",
                   "your onedrive", "files were recently deleted",
                   "network permission", "access from anywhere",
                   "cluster will be paused",
                   "recovered successfully",
                   "security alert", "2-step verification",
                   "pm's message", "constitution",
                   "super stats", "writing activity",
                   "keep writing", "stellar stats",
                   "booking confirmation", "irctc", "train",
                   "clear all your pending bills", "one easy loan"],
    "others": ["unsubscribe", "privacy policy",
               "newsletter", "marketing", "promotional", "promotion",
               "sale", "discount", "offer", "coupon", "deal", "flash sale",
               "you might like", "recommended", "sponsored",
               "trending", "popular", "daily digest", "weekly roundup",
               "facebook", "instagram", "twitter", "linkedin", "youtube",
               "social", "follow", "like", "share", "comment",
               "posted", "uploaded", "pinned", "replied",
               "follower", "new message from",
               "get flat", "shop now", "buy now", "limited time",
               "hurry", "exclusive", "premium", "free shipping",
               "be the first", "new launch", "just launched", "new in",
               "upgrade", "get ready for", "time to", "your makeup",
               "your skin", "your hair", "your beauty",
               "nykaa", "kay beauty", "myntra", "amazon", "flipkart",
               "beauty sale", "beauty launches", "makeup",
               "game", "gaming", "play store", "google play",
               "now on your pc", "now on your",
               "self-care", "wellness", "fitness", "workout",
               "start today", "you can start"],
}


class EmailClassifier:
    _cached_ollama = None
    _cached_cloud = None

    def __init__(self):
        if settings.ollama_enabled:
            if EmailClassifier._cached_ollama is None:
                EmailClassifier._cached_ollama = OllamaClassifier()
            self.backend = EmailClassifier._cached_ollama
        elif settings.groq_api_key:
            if EmailClassifier._cached_cloud is None:
                EmailClassifier._cached_cloud = CloudClassifier()
            self.backend = EmailClassifier._cached_cloud
        else:
            self.backend = None

    def classify(self, subject: str, body_text: str, body_html: str = None,
                 user_id: Optional[int] = None, db: Optional[Session] = None) -> Tuple[str, float]:
        if self.backend:
            try:
                return self.backend.classify(subject or "", body_text or "", body_html,
                                             user_id=user_id, db=db)
            except Exception as e:
                logger.warning("Backend classification failed (%s), using fallback", e)
        return self._rule_fallback(subject or "", clean_body(body_text, body_html))

    def _decode_subject(self, subject: str) -> str:
        if not subject or not subject.startswith("=?"):
            return subject
        try:
            parts = decode_header(subject)
            decoded = []
            for part, charset in parts:
                if isinstance(part, bytes):
                    decoded.append(part.decode(charset or "utf-8", errors="replace"))
                else:
                    decoded.append(str(part))
            return " ".join(decoded)
        except Exception:
            return subject

    def _rule_fallback(self, subject: str, body: str) -> Tuple[str, float]:
        lower = f"{self._decode_subject(subject)} {body}".lower()
        scores = {}
        for cat, kws in FALLBACK_RULES.items():
            scores[cat] = sum(1 for kw in kws if kw in lower)
        tie_priority = ["others", "other_work", "business", "private"]
        best = max(tie_priority, key=lambda c: scores[c])
        score = scores[best]
        if score == 0:
            return "others", 0.65
        boosted = min((score / 3.0) + 0.50, 0.99)
        return best, boosted

    @classmethod
    def reset_cache(cls):
        cls._cached_ollama = None
        cls._cached_cloud = None
