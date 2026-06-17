import pytest
from app.ai.classifier import EmailClassifier


def test_classifier_fallback_business():
    c = EmailClassifier()
    cat, conf = c.classify("Invoice for last month", "Please find attached the invoice")
    assert cat in ("business", "other_work", "private")
    assert conf > 0


def test_classifier_fallback_private():
    c = EmailClassifier()
    cat, _ = c.classify("Family dinner", "Mom invited us this weekend")
    assert cat == "private"


def test_classifier_fallback_other_work():
    c = EmailClassifier()
    cat, _ = c.classify("Your OTP code", "Your bank verification code is 123456")
    assert cat == "other_work"


def test_classifier_fallback_others():
    c = EmailClassifier()
    cat, _ = c.classify("Weekly newsletter", "Here are this week's deals")
    assert cat in ("others", "other_work")


def test_classifier_fallback_spam():
    c = EmailClassifier()
    cat, _ = c.classify("FREE click now", "Claim your prize today limited offer")
    assert cat == "spam"  # AI correctly identifies spam
