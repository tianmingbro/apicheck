import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.stats_service import log_call
from app.models.apikey import APIKey
from app.models.call_log import CallLog
from app.core.config import settings

settings.KEY_FAILURE_THRESHOLD = 3

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_api_key():
    key = MagicMock(spec=APIKey)
    key.id = 1
    key.user_id = 1
    key.is_enabled = True
    key.total_calls = 0
    key.last_used_at = None
    key.error_count = 0
    key.disabled_at = None
    return key

# 辅助函数：生成默认参数（不包含 error_message）
def default_kwargs():
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cost_cents": 0,
        "duration_ms": 0,
    }

@pytest.mark.asyncio
async def test_log_call_success_resets_error_count(mock_db_session, mock_api_key):
    mock_api_key.error_count = 2
    mock_db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_api_key

    await log_call(
        db=mock_db_session,
        request_id="req_123",
        user_id=1,
        api_key_id=1,
        model="gpt-3.5-turbo",
        status_code=200,
        error_message=None,
        **default_kwargs()
    )

    mock_db_session.add.assert_called_once()
    added_log = mock_db_session.add.call_args[0][0]
    assert isinstance(added_log, CallLog)
    assert added_log.request_id == "req_123"
    assert added_log.status_code == 200

    assert mock_api_key.total_calls == 1
    assert mock_api_key.last_used_at is not None
    assert mock_api_key.error_count == 0
    assert mock_api_key.is_enabled is True
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_log_call_failure_increments_error_count(mock_db_session, mock_api_key):
    mock_api_key.error_count = 1
    mock_db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_api_key

    await log_call(
        db=mock_db_session,
        request_id="req_456",
        user_id=1,
        api_key_id=1,
        model="gpt-3.5-turbo",
        status_code=500,
        error_message="Internal error",
        **default_kwargs()
    )

    assert mock_api_key.total_calls == 1
    assert mock_api_key.error_count == 2
    assert mock_api_key.is_enabled is True
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_log_call_failure_reaches_threshold_disables_key(mock_db_session, mock_api_key):
    mock_api_key.error_count = 2
    mock_db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_api_key

    await log_call(
        db=mock_db_session,
        request_id="req_789",
        user_id=1,
        api_key_id=1,
        model="gpt-3.5-turbo",
        status_code=503,
        error_message="Service unavailable",
        **default_kwargs()
    )

    assert mock_api_key.error_count == 3
    assert mock_api_key.is_enabled is False
    assert mock_api_key.disabled_at is not None
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_log_call_already_disabled_key_remains_disabled(mock_db_session, mock_api_key):
    mock_api_key.is_enabled = False
    mock_api_key.disabled_at = datetime.utcnow()
    mock_api_key.error_count = 5
    mock_db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = mock_api_key

    await log_call(
        db=mock_db_session,
        request_id="req_000",
        user_id=1,
        api_key_id=1,
        model="gpt-3.5-turbo",
        status_code=200,
        error_message=None,
        **default_kwargs()
    )

    assert mock_api_key.error_count == 0
    assert mock_api_key.is_enabled is False
    assert mock_api_key.disabled_at is not None
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_log_call_no_api_key_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None

    await log_call(
        db=mock_db_session,
        request_id="req_nokey",
        user_id=1,
        api_key_id=999,
        model="gpt-3.5-turbo",
        status_code=200,
        error_message=None,
        **default_kwargs()
    )

    mock_db_session.add.assert_called_once()

    pass