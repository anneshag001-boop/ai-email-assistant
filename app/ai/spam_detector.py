import re
from typing import Tuple
from app.core.settings import settings


class SpamDetector:
    def __init__(self, threshold: float = None):
        self.threshold = threshold or settings.spam_threshold

    def score(self, subject: str, body: str, sender: str = "",
              recipients: str = "") -> Tuple[float, str, None]:
        rule_score, rule_label = self._rule_based(subject, body)
        return rule_score, rule_label, None

    def _rule_based(self, subject: str, body: str) -> Tuple[float, str]:
        text = f"{subject or ''} {body or ''}".lower()
        score = 0.0
        for kw in self.SPAM_KEYWORDS:
            if re.search(kw, text):
                score += 0.12
        for pat in self.SUSPICIOUS_PATTERNS:
            if re.search(pat, text):
                score += 0.2
        if len(text) < 20:
            score += 0.1
        score = min(score, 1.0)
        return score, "spam" if score >= self.threshold else "not_spam"

    SPAM_KEYWORDS = [
        r"\bclick here\b", r"\bact now\b", r"\blimited time\b",
        r"\bcongratulations\b", r"\bwin(ner|nings)?\b", r"\bfree\b",
        r"\bclaim\b", r"\bprize\b", r"\burgent\b", r"\bviagra\b",
        r"\bcheap\b", r"\bguaranteed\b", r"\bno cost\b", r"\brisk.free\b",
        r"\bdouble your\b", r"\bearn extra\b", r"\bwork from home\b",
        r"\bbuy now\b", r"\bspecial promotion\b",
        r"\blotto\b", r"\blottery\b", r"\bcash bonus\b",
        r"\bcryptocurrency\b", r"\binvestment opportunity\b",
    ]

    SUSPICIOUS_PATTERNS = [
        r"\b\d{6,}\b",
        r"\bhttp[s]?://(?:bit\.ly|tinyurl|goo\.gl)\S+",
        r"\b(?:noreply|no-reply)@",
    ]


class RuleBasedSpamDetector:
    def __init__(self, threshold: float = None):
        self.threshold = threshold or settings.spam_threshold
        self._inner = SpamDetector(threshold=self.threshold)

    def score(self, subject: str, body: str) -> Tuple[float, str]:
        s, l, _ = self._inner.score(subject, body)
        return s, l
