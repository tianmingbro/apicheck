import pytest
import httpx
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.user import User
from app.models.apikey import APIKey
from app.main import app as fastapi_app
from app.db.base import Base
from app.db.session import get_db

# 强制导入所有模型，确保 Base.metadata 被填充
import app.models.user
import app.models.apikey
import app.models.call_log
# 如果 models/__init__.py 已经导入，也可以直接 import app.models

# 使用内存数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# 先创建表（此时 Base.metadata 已包含所有模型）
Base.metadata.create_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db

client = TestClient(fastapi_app)

@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """每个测试后回滚事务，清除数据但保留表结构"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # 覆盖依赖，使用当前 session
    def _get_db():
        try:
            yield session
        finally:
            pass
    fastapi_app.dependency_overrides[get_db] = _get_db

    yield  # 执行测试

    transaction.rollback()
    connection.close()
    # 恢复原有的依赖覆盖
    fastapi_app.dependency_overrides[get_db] = override_get_db

# ---------- 辅助函数 ----------
def get_access_token(username: str = "chat_test_user"):
    resp = client.post("/auth/login", data={"username": username, "password": "testpass"})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    client.post("/auth/register", json={"username": username, "password": "testpass"})
    resp = client.post("/auth/login", data={"username": username, "password": "testpass"})
    return resp.json()["access_token"]

@pytest.fixture
def test_user_and_keys():
    from app.utils.encryption import encrypt_api_key
    token = get_access_token("chat_test_user")
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "chat_test_user").first()
    if not user:
        raise Exception("User not found")
    # 删除已有 keys
    db.query(APIKey).filter(APIKey.user_id == user.id).delete()
    key1 = APIKey(
        user_id=user.id,
        key_value=encrypt_api_key("sk-test-key1"),
        base_url=None,
        is_enabled=True,
        total_calls=0
    )
    key2 = APIKey(
        user_id=user.id,
        key_value=encrypt_api_key("sk-test-key2"),
        base_url=None,
        is_enabled=True,
        total_calls=0
    )
    db.add(key1)
    db.add(key2)
    db.commit()
    user_id = user.id
    key1_id = key1.id
    key2_id = key2.id
    db.close()
    return {"user_id": user_id, "key1_id": key1_id, "key2_id": key2_id}

def test_chat_no_available_keys(test_user_and_keys):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.id == test_user_and_keys["user_id"]).first()
    for key in db.query(APIKey).filter(APIKey.user_id == user.id).all():
        key.is_enabled = False
    db.commit()
    db.close()
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}
    response = client.post("/chat/completions", json=payload, headers=headers)
    assert response.status_code == 503
    assert "No available API key" in response.text

def test_chat_insufficient_quota(test_user_and_keys):
    db = TestingSessionLocal()
    user = db.query(User).filter(User.id == test_user_and_keys["user_id"]).first()
    original_used = user.quota_used
    user.quota_used = user.quota_limit
    user.extra_tokens = 0
    db.commit()
    db.close()
    
    token = get_access_token()  # 使用默认用户名，仍为 "chat_test_user"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}
    
    # patch httpx.Client 避免真实请求（虽然预期不会转发，但安全起见）
    with patch("httpx.Client") as mock_client_class:
        response = client.post("/chat/completions", json=payload, headers=headers)
    
    assert response.status_code == 402
    
    # 恢复配额
    db2 = TestingSessionLocal()
    user2 = db2.query(User).filter(User.id == test_user_and_keys["user_id"]).first()
    user2.quota_used = original_used
    db2.commit()
    db2.close()

# ---------- 测试用例 ----------
def test_chat_completions_success(test_user_and_keys):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        "max_tokens": 100
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hi there!"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock()
        mock_client.post.return_value = mock_response

        response = client.post("/chat/completions", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["content"] == "Hi there!"
    assert data["usage"]["total_tokens"] == 30

@pytest.mark.skip(reason="需要修复 mock 问题")
def test_chat_upstream_timeout(test_user_and_keys):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}

    with patch("httpx.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")

        response = client.post("/chat/completions", json=payload, headers=headers)
        print("Response status:", response.status_code)
        print("Response body:", response.text)
    assert response.status_code == 504
    assert "Upstream API request timeout" in response.text

@pytest.mark.skip(reason="需要修复 mock 问题")
def test_chat_upstream_4xx_error(test_user_and_keys):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}

    with patch("httpx.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
            "401 Client Error", request=MagicMock(), response=mock_response
        ))
        mock_client.post.return_value = mock_response

        response = client.post("/chat/completions", json=payload, headers=headers)

    assert response.status_code == 401
    assert "Invalid API key" in response.text

@pytest.mark.skip(reason="需要修复 mock 问题")
def test_chat_upstream_5xx_error(test_user_and_keys):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}

    with patch("httpx.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
            "503 Server Error", request=MagicMock(), response=mock_response
        ))
        mock_client.post.return_value = mock_response

        response = client.post("/chat/completions", json=payload, headers=headers)

    assert response.status_code == 503
    assert "Service Unavailable" in response.text

def test_chat_unauthorized_no_token():
    payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}
    response = client.post("/chat/completions", json=payload)
    assert response.status_code == 401