import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from faker import Faker

fake = Faker()

# 全局 mock：在导入任何 app 模块之前就替换掉 redis_client 中的全局脚本变量
# 使用 autouse fixture 确保早期生效
@pytest.fixture(autouse=True, scope="function")
def mock_redis_script():
    with patch("app.utils.redis_client.SLIDING_WINDOW_SCRIPT", new_callable=AsyncMock) as mock_script:
        # 让脚本返回 (allowed=1, count=0, retry_after=0) 表示允许请求
        mock_script.return_value = (1, 0, 0)
        yield

@pytest.mark.asyncio
async def test_full_user_journey(client):
    # 注册
    username = fake.user_name()
    password = "Test123!"
    reg_resp = await client.post("/auth/register", json={"username": username, "password": password})
    assert reg_resp.status_code == 201

    # 登录
    login_resp = await client.post("/auth/login", data={"username": username, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 添加 API Key
    fake_key = "sk-test1234567890abcdef"
    add_key_resp = await client.post("/keys", json={"key_value": fake_key}, headers=headers)
    assert add_key_resp.status_code == 201
    key_id = add_key_resp.json()["id"]

    # 模拟上游聊天接口
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={
            "id": "chatcmpl-123",
            "choices": [{"message": {"content": "Hello from mock"}}],
            "usage": {"total_tokens": 10}
        })
        mock_post.return_value = mock_response

        chat_resp = await client.post("/chat/completions", headers=headers, json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hi"}]
        })
        assert chat_resp.status_code == 200
        data = await chat_resp.json()
        assert data["choices"][0]["message"]["content"] == "Hello from mock"

    # 删除 API Key
    del_resp = await client.delete(f"/keys/{key_id}", headers=headers)
    assert del_resp.status_code == 200

    await asyncio.sleep(0.1)