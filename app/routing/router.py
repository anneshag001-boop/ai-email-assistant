from typing import Dict, Any


def route_email(spam_label: str, category_label: str, category_confidence: float,
                priority_score: float) -> Dict[str, Any]:
    is_spam = (spam_label == "spam") or (category_label == "spam")

    if is_spam:
        return {"routed_folder": "Spam", "routed_action": "move_to_trash_after_1d"}

    container_map = {
        "private": ("Private", "move_to_folder"),
        "business": ("Business", "move_to_folder"),
        "other_work": ("Other Work", "archive"),
        "others": ("Others", "archive"),
    }

    folder, action = container_map.get(category_label, ("Others", "archive"))
    return {"routed_folder": folder, "routed_action": action}
