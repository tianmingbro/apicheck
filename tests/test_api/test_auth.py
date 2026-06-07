# tests/test_api/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from fastapi import Depends, FastAPI  # 新增导入
from app.api import deps  # 导入依赖模块

# 使用内存数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"   # 或者 ":memory:" 但 SQLite 内存模式对多线程不太友好，使用文件也可以
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_register_success():
    response = client.post("/auth/register", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["role"] == "user"
    assert "id" in data

def test_register_duplicate_username():
    # 先注册一个用户
    client.post("/auth/register", json={"username": "duplicate", "password": "pass"})
    # 再次注册相同用户名
    response = client.post("/auth/register", json={"username": "duplicate", "password": "pass"})
    assert response.status_code == 400
    assert "Username already registered" in response.text

def test_login_success():
    # 先注册
    client.post("/auth/register", json={"username": "loginuser", "password": "loginpass"})
    # 登录
    response = client.post("/auth/login", data={"username": "loginuser", "password": "loginpass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password():
    client.post("/auth/register", json={"username": "wrongpass", "password": "correct"})
    response = client.post("/auth/login", data={"username": "wrongpass", "password": "wrong"})
    assert response.status_code == 401

def test_login_nonexistent_user():
    response = client.post("/auth/login", data={"username": "nonexistent", "password": "any"})
    assert response.status_code == 401

import asyncio
from app.api.deps import get_current_user
def test_get_current_user_dependency():
    # 先注册并登录获取 token
    client.post("/auth/register", json={"username": "me", "password": "secret"})
    login_resp = client.post("/auth/login", data={"username": "me", "password": "secret"})
    token = login_resp.json()["access_token"]
    
    # 获取数据库会话
    db = next(override_get_db())
    
    # 直接运行异步函数获取当前用户
    user = asyncio.run(get_current_user(token=token, db=db))
    assert user.username == "me"