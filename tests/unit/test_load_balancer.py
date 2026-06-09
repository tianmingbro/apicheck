import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.core.load_balancer import LoadBalancer
from app.models.apikey import APIKey

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def sample_keys():
    keys = []
    for i in range(3):
        key = MagicMock(spec=APIKey)
        key.id = i + 1
        key.user_id = 1
        key.is_enabled = True
        key.total_calls = i * 10
        keys.append(key)
    return keys

def test_round_robin_strategy(mock_db_session, sample_keys):
    mock_db_session.query().filter().all.return_value = sample_keys
    lb = LoadBalancer(mock_db_session, strategy="round_robin")
    
    # 第一次调用返回第一个key
    selected = lb.get_next_key(1)
    assert selected.id == 1
    # 第二次调用返回第二个key
    selected = lb.get_next_key(1)
    assert selected.id == 2
    # 第三次调用返回第三个key
    selected = lb.get_next_key(1)
    assert selected.id == 3
    # 第四次调用回到第一个key
    selected = lb.get_next_key(1)
    assert selected.id == 1

def test_least_used_strategy(mock_db_session, sample_keys):
    # 修改total_calls: key1=100, key2=50, key3=0
    sample_keys[0].total_calls = 100
    sample_keys[1].total_calls = 50
    sample_keys[2].total_calls = 0
    mock_db_session.query().filter().all.return_value = sample_keys
    
    lb = LoadBalancer(mock_db_session, strategy="least_used")
    selected = lb.get_next_key(1)
    # 应选择 total_calls 最小的 key3
    assert selected.id == 3

def test_no_available_keys(mock_db_session):
    mock_db_session.query().filter().all.return_value = []
    lb = LoadBalancer(mock_db_session)
    selected = lb.get_next_key(1)
    assert selected is None