import logging

logger = logging.getLogger(__name__)


def scheduled_retrain():
    logger.info("SLM-based classifier does not require retraining")
