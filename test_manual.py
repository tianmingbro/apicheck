import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_login():
    # 注册
    r = client.post("/auth/register", json={"username": "testuser", "password": "testpass"})
    print("Register:", r.status_code, r.text)
    # 登录
    r = client.post("/auth/login", data={"username": "testuser", "password": "testpass"})
    print("Login:", r.status_code, r.text)
    return r.json().get("access_token")

if __name__ == "__main__":
    token = test_register_login()
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        # 尝试调用聊天接口
        payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hi"}]}
        r = client.post("/chat/completions", json=payload, headers=headers)
        print("Chat:", r.status_code, r.text)
    else:
        print("Failed to get token") 