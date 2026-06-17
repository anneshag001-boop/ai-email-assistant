import logging
from typing import Tuple, Optional
from app.core.settings import settings

logger = logging.getLogger(__name__)

class HFEmailClassifier:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.hf_model_name
        self._tokenizer = None
        self._model = None
        self._pipeline = None
        self._loaded = False
        # Ensure labels match exactly with what the router expects
        self._labels = ["business", "private", "important", "other_work", "others", "spam"]

    def load(self):
        if self._loaded:
            return
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._pipeline = pipeline(
                "text-classification",
                model=self._model,
                tokenizer=self._tokenizer,
                max_length=512,
                truncation=True,
                top_k=None,
            )
            self._loaded = True
            logger.info("Hugging Face model '%s' loaded", self.model_name)
        except Exception as e:
            logger.warning("Failed to load HF model '%s': %s", self.model_name, e)
            self._loaded = False

    def is_loaded(self) -> bool:
        return self._loaded

    def classify(self, text: str) -> Tuple[str, float]:
        if not self._loaded:
            self.load()
            
        # FIX: If it still failed to load, don't return 0.0. 
        # Raise an exception so the main classifier knows to use the fallback rules.
        if not self._loaded:
            raise RuntimeError("HuggingFace pipeline is not active.")

        try:
            results = self._pipeline(text, max_length=512, truncation=True)
            if isinstance(results, list) and isinstance(results[0], list):
                results = results[0]
            best = max(results, key=lambda x: x["score"])
            
            # Map raw model output to our standard categories if necessary
            label = best["label"].lower()
            if label not in self._labels:
                label = "others"
                
            return label, float(best["score"])
        except Exception as e:
            logger.error("HF classification error: %s", e)
            # FIX: Again, raise an error to trigger the safe fallback, don't return junk data.
            raise RuntimeError(f"HF Inference failed: {e}")