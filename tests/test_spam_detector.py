import pytest
from app.ai.spam_detector import SpamDetector, RuleBasedSpamDetector


def test_spam_detector_detects_spam():
    from app.core.settings import settings
    original = settings.spam_threshold
    settings.spam_threshold = 0.3
    d = SpamDetector()
    s, l, r = d.score("Free prize click here", "Claim your reward now")
    settings.spam_threshold = original
    assert l == "spam"
    assert s > 0.3
    assert r is None


def test_spam_detector_clean():
    d = SpamDetector()
    s, l, r = d.score("Meeting agenda", "Let's discuss the project")
    assert l == "not_spam"


def test_rule_based_backward_compat():
    d = RuleBasedSpamDetector(threshold=0.5)
    s, l = d.score("Free lottery winner", "Claim cash bonus now")
    assert l == "spam"


def test_rule_based_clean():
    d = RuleBasedSpamDetector(threshold=0.5)
    s, l = d.score("Status update", "All good here")
    assert l == "not_spam"


def test_spam_detector_with_sender():
    d = SpamDetector()
    s, l, r = d.score("Invoice", "Payment due", sender="noreply@scam.com")
    assert l == "not_spam"
