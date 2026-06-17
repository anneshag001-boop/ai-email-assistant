import pytest
from app.ai.spamassassin_client import SpamAssassinClient


def test_spamassassin_init():
    client = SpamAssassinClient(host="127.0.0.1", port=783)
    assert client.host == "127.0.0.1"
    assert client.port == 783


def test_spamassassin_parse_response():
    client = SpamAssassinClient()
    raw = "SPAMD/1.5 0 EX_OK\r\nSpam: False ; 2.5 / 5.0\r\n\r\nContent-Length: 0\r\n\r\n"
    result = client._parse_response(raw)
    assert "score" in result
    assert result["score"] == 2.5


def test_spamassassin_connection_refused_fallback():
    client = SpamAssassinClient(host="127.0.0.1", port=1783, timeout=1)
    score, label, report = client.score("test", "hello world")
    assert label == "not_spam"
    assert score == 0.0


def test_spam_detector_with_spamassassin_disabled():
    from app.core.settings import settings
    from app.ai.spam_detector import SpamDetector
    original = settings.spam_threshold
    settings.spam_threshold = 0.3
    detector = SpamDetector()
    score, label, report = detector.score("Free prize click here", "Claim your reward")
    settings.spam_threshold = original
    assert label == "spam"
    assert report is None
