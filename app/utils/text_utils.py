import re


def detect_language(text: str) -> str:
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "en"


def count_words(text: str) -> int:
    return len(text.split())


def strip_urls(text: str) -> str:
    return re.sub(r"http[s]?://\S+", "", text)


def strip_emails(text: str) -> str:
    return re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "", text)
