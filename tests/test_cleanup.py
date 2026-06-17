from app.core.settings import settings


def test_spam_retention_setting():
    assert settings.spam_retention_days == 30


def test_cleanup_runs():
    from app.jobs.cleanup import cleanup_spam
    try:
        cleanup_spam()
    except Exception as e:
        pytest.fail(f"cleanup_spam raised: {e}")

import pytest
