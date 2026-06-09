import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.chat_service import ChatService
from app.models.user import User
from app.models.apikey import APIKey
from app.core.load_balancer import LoadBalancer

@pytest.fixture
def mock_db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_current_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user

@pytest.fixture
def mock_api_key():
    key = MagicMock(spec=APIKey)
    key.id = 1
    key.key_value = "encrypted_key_here"
    key.base_url = None
    key.is_enabled = True
    return key

@pytest.fixture
def mock_load_balancer_instance(mock_api_key):
    lb = MagicMock(spec=LoadBalancer)
    lb.get_next_key.return_value = mock_api_key
    return lb

@patch("app.services.chat_service._get_client")
@patch("app.services.chat_service.log_call")
async def test_process_chat_request_success(mock_log_call, mock_get_client, mock_db_session, mock_current_user, mock_load_balancer_instance):
    # 创建模拟的响应对象（同步方法）
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={
        "id": "chatcmpl-123",
        "choices": [{"message": {"content": "Hello"}}],
        "usage": {"total_tokens": 10}
    })
    mock_response.raise_for_status = MagicMock()
    
    # 模拟客户端
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    with patch("app.services.chat_service.LoadBalancer", return_value=mock_load_balancer_instance):
        with patch("app.services.chat_service.check_and_deduct_quota", return_value=True):
            with patch("app.services.chat_service.decrypt_api_key", return_value="sk-real-key"):
                service = ChatService(mock_db_session, mock_current_user)
                result = await service.process_chat_request({
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hi"}]
                })
                assert result["choices"][0]["message"]["content"] == "Hello"
                mock_log_call.assert_called_once()

                
@pytest.mark.asyncio
async def test_process_chat_request_no_available_keys(mock_db_session, mock_current_user):
    mock_lb = MagicMock(spec=LoadBalancer)
    mock_lb.get_next_key.return_value = None
    with patch("app.services.chat_service.LoadBalancer", return_value=mock_lb):
        service = ChatService(mock_db_session, mock_current_user)
        with pytest.raises(HTTPException) as exc:
            await service.process_chat_request({"model": "gpt", "messages": []})
        assert exc.value.status_code == 503
        assert "No available API keys" in exc.value.detail

@pytest.mark.asyncio
async def test_process_chat_request_insufficient_quota(mock_db_session, mock_current_user, mock_api_key):
    mock_lb = MagicMock(spec=LoadBalancer)
    mock_lb.get_next_key.return_value = mock_api_key
    with patch("app.services.chat_service.LoadBalancer", return_value=mock_lb):
        with patch("app.services.chat_service.check_and_deduct_quota", return_value=False):
            service = ChatService(mock_db_session, mock_current_user)
            with pytest.raises(HTTPException) as exc:
                await service.process_chat_request({"model": "gpt", "messages": []})
            assert exc.value.status_code == 402
            assert "Insufficient quota" in exc.value.detail

@pytest.mark.asyncio
async def test_process_chat_request_upstream_timeout(mock_db_session, mock_current_user, mock_load_balancer_instance):
    with patch("app.services.chat_service.LoadBalancer", return_value=mock_load_balancer_instance):
        with patch("app.services.chat_service.check_and_deduct_quota", return_value=True):
            with patch("app.services.chat_service.decrypt_api_key", return_value="sk-key"):
                mock_client = AsyncMock()
                mock_client.post.side_effect = httpx.TimeoutException("Timeout")
                with patch("app.services.chat_service._get_client", return_value=mock_client):
                    with patch("app.services.chat_service.log_call") as mock_log_call:
                        service = ChatService(mock_db_session, mock_current_user)
                        with pytest.raises(HTTPException) as exc:
                            await service.process_chat_request({"model": "gpt", "messages": []})
                        assert exc.value.status_code == 504
                        assert mock_log_call.called

@pytest.mark.asyncio
async def test_process_chat_request_upstream_4xx(mock_db_session, mock_current_user, mock_load_balancer_instance):
    with patch("app.services.chat_service.LoadBalancer", return_value=mock_load_balancer_instance):
        with patch("app.services.chat_service.check_and_deduct_quota", return_value=True):
            with patch("app.services.chat_service.decrypt_api_key", return_value="sk-key"):
                mock_client = AsyncMock()
                # 模拟 HTTPStatusError
                async def raise_http_error(*args, **kwargs):
                    response = MagicMock()
                    response.status_code = 401
                    response.text = "Invalid API key"
                    raise httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=response)
                mock_client.post.side_effect = raise_http_error
                with patch("app.services.chat_service._get_client", return_value=mock_client):
                    with patch("app.services.chat_service.log_call") as mock_log_call:
                        service = ChatService(mock_db_session, mock_current_user)
                        with pytest.raises(HTTPException) as exc:
                            await service.process_chat_request({"model": "gpt", "messages": []})
                        assert exc.value.status_code == 401
                        assert "Invalid API key" in exc.value.detail