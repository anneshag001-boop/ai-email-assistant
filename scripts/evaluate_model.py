#!/usr/bin/env python
import argparse, pickle, logging
from sklearn.metrics import classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_SAMPLES = [
    ("meeting agenda for project alpha", "business"),
    ("urgent please respond immediately", "important"),
    ("family gathering this weekend", "private"),
    ("claim your free prize now", "spam"),
    ("timesheet approval pending", "other_work"),
    ("your package has been delivered", "others"),
    ("critical server outage notification", "important"),
    ("buy now limited quantities", "spam"),
    ("jira ticket assigned to you", "other_work"),
    ("quarterly financial report", "business"),
]


def evaluate(model_path: str, vectorizer_path: str):
    with open(vectorizer_path, "rb") as f:
        vectorizer = pickle.load(f)
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    texts, true = zip(*TEST_SAMPLES)
    X = vectorizer.transform(texts)
    preds = model.predict(X)
    proba = model.predict_proba(X).max(axis=1)

    for t, tr, pr, conf in zip(texts, true, preds, proba):
        mark = "✓" if tr == pr else "✗"
        logger.info("  [%s] true=%-12s pred=%-12s conf=%.2f | %s", mark, tr, pr, conf, t[:50])

    logger.info("\n%s", classification_report(true, preds, zero_division=0))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="data/models/classifier_model.pkl")
    parser.add_argument("--vectorizer", default="data/models/vectorizer.pkl")
    args = parser.parse_args()
    evaluate(args.model, args.vectorizer)
