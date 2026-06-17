#!/usr/bin/env python
import argparse, os, pickle, logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_DATA = {
    "business": [
        "meeting scheduled for tomorrow at 10am",
        "please find attached the invoice for last month",
        "project proposal review on Friday",
        "client requested a follow-up call",
        "purchase order confirmed for Q3",
        "contract needs your signature",
    ],
    "private": [
        "family dinner this Saturday",
        "thanks for the birthday wishes",
        "photo album from our vacation",
        "invitation to the wedding",
        "mom asked about the weekend plans",
    ],
    "important": [
        "urgent: action required on your account",
        "deadline extended until Friday",
        "critical security update needed",
        "ASAP: please respond to this message",
    ],
    "other_work": [
        "timesheet reminder for this week",
        "sprint planning on Monday",
        "standup at 9:30am tomorrow",
        "jira ticket updated",
        "pull request ready for review",
    ],
    "others": [
        "newsletter: tech digest this week",
        "your order has been shipped",
        "weekly deals from our store",
    ],
    "spam": [
        "congratulations you won a prize",
        "click here to claim your reward",
        "limited time offer buy now",
        "work from home earn thousands",
        "lottery winner claim your cash",
    ],
}


def train(output_dir: str = "data/models"):
    os.makedirs(output_dir, exist_ok=True)

    texts, labels = [], []
    for label, samples in SAMPLE_DATA.items():
        for s in samples:
            texts.append(s)
            labels.append(label)

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(vectorizer.transform(X_test))
    logger.info("Classification report:\n%s", classification_report(y_test, y_pred, zero_division=0))

    with open(os.path.join(output_dir, "vectorizer.pkl"), "wb") as f:
        pickle.dump(vectorizer, f)
    with open(os.path.join(output_dir, "classifier_model.pkl"), "wb") as f:
        pickle.dump(model, f)
    logger.info("Model saved to %s", output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/models")
    args = parser.parse_args()
    train(args.output)
