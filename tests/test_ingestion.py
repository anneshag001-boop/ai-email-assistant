import pytest
from datetime import datetime
from app.ingestion import NormalizedEmail
from app.preprocessing.parser import parse_sender, parse_recipients
from app.preprocessing.cleaner import clean_body, strip_html, clean_signatures


def test_normalized_email():
    e = NormalizedEmail(provider="test", message_id="1", sender="a@b.com", subject="Hi", body_text="Hello")
    assert e.provider == "test"
    assert e.to_dict()["sender"] == "a@b.com"


def test_parse_sender_with_name():
    assert parse_sender("John <john@test.com>") == "john@test.com"


def test_parse_sender_bare():
    assert parse_sender("john@test.com") == "john@test.com"


def test_parse_recipients():
    r = parse_recipients("a@b.com; c@d.com")
    assert r == ["a@b.com", "c@d.com"]


def test_strip_html():
    r = strip_html("<html><p>Hello <b>World</b></p></html>")
    assert "Hello" in r and "World" in r
    assert "<" not in r


def test_clean_body_removes_quotes():
    r = clean_body("Hello\n\nOn Mon, 1 Jan wrote:\n> quoted\n-- \nSig", None)
    assert "Hello" in r
    assert "quoted" not in r


def test_clean_signatures():
    r = clean_signatures("Line 1\n-- \nSignature")
    assert "Line 1" in r
    assert "Signature" not in r


def test_email_to_dict_with_dt():
    dt = datetime(2024, 6, 1, 12, 0)
    e = NormalizedEmail(provider="gmail", message_id="abc", sender="x@y.com", received_at=dt)
    assert e.to_dict()["received_at"] == "2024-06-01T12:00:00"
