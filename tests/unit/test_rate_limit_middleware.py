# tests/unit/test_rate_limit_middleware.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.middleware.rate_limit import RateLimitMiddleware, RATE_LIMIT_CONFIG
from app.core.config import settings
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User, UserRole

# 创建测试应用
def create_test_app():
    app = FastAPI()
    
    @app.get("/chat/completions")
    async def chat_endpoint():
        return {"message": "ok"}
    
    @app.get("/keys/")
    async def keys_endpoint():
        return {"message": "keys"}
    
    @app.get("/public")
    async def public_endpoint():
        return {"message": "public"}
    
    app.add_middleware(RateLimitMiddleware)
    return app

@pytest.fixture
def client():
    return TestClient(create_test_app())

@pytest.mark.asyncio
async def test_rate_limit_middleware_allowed(client):
    """测试未超限时正常通过，并返回响应头"""
    with patch("app.middleware.rate_limit.sliding_window_rate_limit", new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 5, 0)
        # 模拟中间件的 get_user_id_from_token 方法，直接返回用户名
        with patch("app.middleware.rate_limit.RateLimitMiddleware.get_user_id_from_token", new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = "testuser"
            response = client.get("/chat/completions", headers={"Authorization": "Bearer test_token"})
            assert response.status_code == 200
            assert response.headers.get("X-RateLimit-Limit") == "10"
            assert response.headers.get("X-RateLimit-Remaining") == "5"
            assert "Retry-After" not in response.headers
            mock_rate_limit.assert_called_once()
            args = mock_rate_limit.call_args[0]
            assert "rate_limit:user:testuser:/chat/completions" in args[0]

@pytest.mark.asyncio
async def test_rate_limit_middleware_no_token_uses_ip(client):
    """测试无 token 时使用 IP 作为标识"""
    with patch("app.middleware.rate_limit.sliding_window_rate_limit", new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 2, 0)
        response = client.get("/chat/completions")  # 无 Authorization
        assert response.status_code == 200
        mock_rate_limit.assert_called_once()
        args = mock_rate_limit.call_args[0]
        # TestClient 的默认 client.host 为 'testclient'
        assert "rate_limit:ip:testclient:/chat/completions" in args[0]

@pytest.mark.asyncio
async def test_rate_limit_middleware_exceeded(client):
    """测试超出限制时返回 429 并包含 Retry-After"""
    with patch("app.middleware.rate_limit.sliding_window_rate_limit", new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (False, 10, 30)  # 被拒绝，当前计数=10，需等待30秒
        
        response = client.get("/chat/completions", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == 429
        assert response.headers.get("X-RateLimit-Limit") == "10"
        assert response.headers.get("X-RateLimit-Remaining") == "0"
        assert response.headers.get("Retry-After") == "30"
        assert response.json()["detail"] == "Too Many Requests"


@pytest.mark.asyncio
async def test_rate_limit_middleware_skip_public_endpoint(client):
    """测试不在限流配置中的端点直接放行，不调用 Redis"""
    with patch("app.middleware.rate_limit.sliding_window_rate_limit", new_callable=AsyncMock) as mock_rate_limit:
        response = client.get("/public")
        assert response.status_code == 200
        mock_rate_limit.assert_not_called()

@pytest.mark.asyncio
async def test_rate_limit_middleware_different_paths_have_separate_keys(client):
    """测试不同路径使用不同的 Redis key"""
    with patch("app.middleware.rate_limit.sliding_window_rate_limit", new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 1, 0)
        
        response1 = client.get("/chat/completions", headers={"Authorization": "Bearer token1"})
        response2 = client.get("/keys/", headers={"Authorization": "Bearer token1"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert mock_rate_limit.call_count == 2
        # 验证两次调用的 key 不同
        call_args_list = mock_rate_limit.call_args_list
        assert "/chat/completions" in call_args_list[0][0][0]
        assert "/keys/" in call_args_list[1][0][0]

@pytest.mark.asyncio
async def test_rate_limit_middleware_member_uniqueness(client):
    """测试每次请求 member 唯一，确保窗口计数准确"""
    with patch("app.middleware.rate_limit.sliding_window_rate_limit", new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 1, 0)
        
        response1 = client.get("/chat/completions", headers={"Authorization": "Bearer token_uuid"})
        response2 = client.get("/chat/completions", headers={"Authorization": "Bearer token_uuid"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        # 验证 member 参数（第4个参数）不为空且不同
        member1 = mock_rate_limit.call_args_list[0][0][3]
        member2 = mock_rate_limit.call_args_list[1][0][3]
        assert member1 != member2

@pytest.mark.asyncio
async def test_rate_limit_middleware_with_valid_token_uses_user_id(client):
    with patch("app.middleware.rate_limit.sliding_window_rate_limit", new_callable=AsyncMock) as mock_rate_limit:
        with patch("app.middleware.rate_limit.jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.return_value = {"sub": "alice"}
            mock_rate_limit.return_value = (True, 1, 0)
            response = client.get("/chat/completions", headers={"Authorization": "Bearer valid.token"})
            assert response.status_code == 200
            mock_rate_limit.assert_called_once()
            # key 应包含 user:alice
            assert "rate_limit:user:alice:" in mock_rate_limit.call_args[0][0]