from app.preprocessing.cleaner import clean_body


def compute_confidence(spam_score: float, category_confidence: float) -> float:
    return round(min(category_confidence * (1.0 - spam_score), 1.0), 4)
