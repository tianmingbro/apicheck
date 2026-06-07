# tests/test_api/test_keys.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_api.test_auth import override_get_db, setup_database   # 复用测试数据库

client = TestClient(app)

def test_crud_keys():
    # 1. 注册用户
    client.post("/auth/register", json={"username": "keyuser", "password": "pass"})
    # 2. 登录
    login_resp = client.post("/auth/login", data={"username": "keyuser", "password": "pass"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. 添加 API Key
    add_resp = client.post("/keys/", json={"key_value": "sk-test1234567890"}, headers=headers)
    assert add_resp.status_code == 201
    data = add_resp.json()
    key_id = data["id"]
    # ✅ 修正期望值：前4位 sk-t，后4位 7890，中间9个星号
    assert data["key"] == "sk-t*********7890"
    assert data["is_enabled"] is True

    # 4. 列出 keys
    list_resp = client.get("/keys/", headers=headers)
    assert list_resp.status_code == 200
    keys = list_resp.json()
    assert len(keys) == 1
    assert keys[0]["id"] == key_id
    assert keys[0]["key"] == "sk-t*********7890"

    # 5. 删除 key
    del_resp = client.delete(f"/keys/{key_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "API Key deleted successfully"

    # 6. 再次列出，应为空
    list_resp2 = client.get("/keys/", headers=headers)
    assert len(list_resp2.json()) == 0
    
def test_delete_nonexistent_key():
    client.post("/auth/register", json={"username": "deluser", "password": "pass"})
    login_resp = client.post("/auth/login", data={"username": "deluser", "password": "pass"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete("/keys/9999", headers=headers)
    assert resp.status_code == 404
    assert "API Key not found" in resp.text