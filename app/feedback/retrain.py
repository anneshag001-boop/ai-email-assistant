import logging

logger = logging.getLogger(__name__)


def retrain_classifier(db) -> bool:
    logger.info("SLM-based classifier does not require retraining")
    return True
