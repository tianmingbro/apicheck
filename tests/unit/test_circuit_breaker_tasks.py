from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.orm import Session
from app.models.apikey import APIKey
from app.tasks.circuit_breaker import disable_failed_keys, recover_disabled_keys

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    # 模拟查询结果
    failing_keys = [
        MagicMock(spec=APIKey, id=1, is_enabled=True, error_count=5, disabled_at=None),
        MagicMock(spec=APIKey, id=2, is_enabled=True, error_count=10, disabled_at=None),
    ]
    recoverable_keys = [
        MagicMock(spec=APIKey, id=3, is_enabled=False, disabled_at=datetime.utcnow() - timedelta(seconds=400), error_count=5),
    ]
    db.query().filter().all.side_effect = [failing_keys, recoverable_keys]
    return db

def test_disable_failed_keys(mock_db):
    with patch("app.tasks.circuit_breaker.SessionLocal", return_value=mock_db):
        disable_failed_keys()
        for key in mock_db.query().filter().all():
            assert key.is_enabled is False
            assert key.disabled_at is not None
        mock_db.commit.assert_called_once()

def test_recover_disabled_keys(mock_db):
    key = mock_db.query().filter().all()[0]
    key.disabled_at = datetime.utcnow() - timedelta(seconds=400)  # 超时已过
    with patch("app.tasks.circuit_breaker.SessionLocal", return_value=mock_db):
        with patch("app.core.config.settings.KEY_RECOVERY_TIMEOUT_SECONDS", 300):
            recover_disabled_keys()
            assert key.is_enabled is True