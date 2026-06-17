from typing import Dict, List
from dataclasses import dataclass


@dataclass
class RoutingRule:
    condition: str
    target_folder: str
    priority: int


FOLDER_MAP: Dict[str, str] = {
    "spam": "Spam",
    "private": "Private",
    "business": "Business",
    "other_work": "Other Work",
    "others": "Others",
}

DEFAULT_RULES: List[RoutingRule] = [
    RoutingRule("spam_label == 'spam' or category_label == 'spam'", "spam", 100),
    RoutingRule("category_label == 'business'", "business", 80),
    RoutingRule("category_label == 'private'", "private", 70),
    RoutingRule("category_label == 'other_work'", "other_work", 60),
    RoutingRule("category_label == 'others'", "others", 50),
]
