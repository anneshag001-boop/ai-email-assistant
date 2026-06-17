import re
from bs4 import BeautifulSoup
from typing import Optional


def strip_html(html_content: Optional[str]) -> str:
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def clean_signatures(body: str) -> str:
    lines = body.split("\n")
    result = []
    for line in lines:
        lower = line.strip().lower()
        if lower in ("-- ", "--", "___", "---", "~~~~"):
            break
        if lower.startswith("sent from my") or lower.startswith("sent from "):
            break
        if re.match(r"^on\s+.+\s+wrote:", lower):
            break
        if re.match(r"^>+\s", line):
            continue
        result.append(line)
    return "\n".join(result).strip()


def clean_quoted_replies(body: str) -> str:
    lines = body.split("\n")
    result = []
    for line in lines:
        if re.match(r"^On\s+.+\s+wrote:$", line.strip()):
            break
        if line.strip().startswith(">"):
            continue
        if re.match(r"^-{2,}Original Message-{2,}", line.strip(), re.IGNORECASE):
            break
        result.append(line)
    return "\n".join(result).strip()


def clean_body(body_text: Optional[str], body_html: Optional[str]) -> str:
    raw = body_text or ""
    if not raw and body_html:
        raw = strip_html(body_html)
    raw = clean_quoted_replies(raw)
    raw = clean_signatures(raw)
    return re.sub(r"\s+", " ", raw).strip()
