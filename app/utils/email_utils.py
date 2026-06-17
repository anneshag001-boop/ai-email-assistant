import re
from typing import List


def extract_email_addresses(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)


def is_unsubscribe_header(headers: dict) -> bool:
    return bool(headers.get("list-unsubscribe", ""))


def truncate_body(body: str, max_chars: int = 5000) -> str:
    return body[:max_chars] if body else ""


def detect_provider(email_addr: str) -> str:
    domain = email_addr.lower().split("@")[-1] if "@" in email_addr else ""
    if "gmail" in domain:
        return "gmail"
    if any(d in domain for d in ("outlook", "hotmail", "live", "microsoft")):
        return "outlook"
    return "imap"
