import re
from email.utils import parseaddr
from typing import Optional
from app.ingestion import NormalizedEmail


def parse_sender(raw_sender: str) -> str:
    _, addr = parseaddr(raw_sender)
    return addr if addr else raw_sender


def parse_recipients(raw_recipients: str) -> list:
    if not raw_recipients:
        return []
    return [parseaddr(p.strip())[1] for p in re.split(r"[;,]", raw_recipients) if parseaddr(p.strip())[1]]


def extract_domain(email_addr: str) -> Optional[str]:
    match = re.search(r"@([\w.-]+)", email_addr)
    return match.group(1) if match else None


def parse_email(normalized: NormalizedEmail) -> NormalizedEmail:
    normalized.sender = parse_sender(normalized.sender)
    return normalized
