import hashlib
from typing import Optional, Set
from app.ingestion import NormalizedEmail
from app.storage.repository import EmailRepository


def content_hash(email: NormalizedEmail) -> str:
    raw = f"{email.subject or ''}{email.body_text or ''}{email.sender or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_seen_hashes: Set[str] = set()


def is_duplicate_in_session(hash_str: str) -> bool:
    return hash_str in _seen_hashes


def mark_seen(hash_str: str):
    _seen_hashes.add(hash_str)


def reset():
    _seen_hashes.clear()


def is_duplicate_in_db(email: NormalizedEmail, repo: EmailRepository) -> bool:
    return repo.get_email_by_message_id(email.message_id, email.provider) is not None
