import pickle
import os
import logging
from typing import Optional
from app.core.settings import settings

logger = logging.getLogger(__name__)


class ModelLoader:
    def __init__(self):
        self.spam_model_path = settings.spam_model_path
        self.classifier_path = settings.classifier_model_path
        self.vectorizer_path = settings.vectorizer_path

    def load_spam_model(self) -> Optional[object]:
        if not os.path.exists(self.spam_model_path):
            return None
        with open(self.spam_model_path, "rb") as f:
            return pickle.load(f)

    def load_classifier(self) -> Optional[object]:
        if not os.path.exists(self.classifier_path):
            return None
        with open(self.classifier_path, "rb") as f:
            return pickle.load(f)

    def load_vectorizer(self) -> Optional[object]:
        if not os.path.exists(self.vectorizer_path):
            return None
        with open(self.vectorizer_path, "rb") as f:
            return pickle.load(f)

    def save_classifier(self, model, vectorizer):
        os.makedirs(os.path.dirname(self.classifier_path), exist_ok=True)
        with open(self.classifier_path, "wb") as f:
            pickle.dump(model, f)
        with open(self.vectorizer_path, "wb") as f:
            pickle.dump(vectorizer, f)
        logger.info("Classifier saved to %s", self.classifier_path)
