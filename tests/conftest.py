# tests/conftest.py
import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User, UserRole
from app.models.plan import Plan

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.main import app as original_app
from app.middleware.rate_limit import RateLimitMiddleware

@pytest.fixture
async def client():
    # 创建新的 FastAPI 实例，复用原路由，但排除限流中间件
    app = FastAPI()
    app.router = original_app.router
    # 复制中间件（排除 RateLimitMiddleware）
    for middleware in original_app.user_middleware:
        if middleware.cls != RateLimitMiddleware:
            app.add_middleware(middleware.cls, **middleware.options)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
load_dotenv()
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

os.environ.setdefault("ALIPAY_APP_ID", "2021000123456789")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key")
os.environ.setdefault("ENCRYPTION_KEY", "test_encryption_key")

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 异步版本的 mock 用户依赖
async def mock_get_current_user():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.id == 1).first()
    db.close()
    if not user:
        raise RuntimeError("Test user not found in database")
    return user

app.dependency_overrides[get_current_user] = mock_get_current_user

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # 创建测试用户
        if not db.query(User).filter(User.id == 1).first():
            user = User(
                id=1,
                username="testuser",
                hashed_password="fake",
                role=UserRole.USER,
                quota_limit=1000,
                quota_used=0,
                extra_tokens=0,
            )
            db.add(user)
        # 创建测试套餐
        if not db.query(Plan).filter(Plan.id == 1).first():
            plan = Plan(
                id=1,
                name="Test Plan",
                code="test",
                price_cents=100,
                quota=1000,
                is_active=True,
                features={}
            )
            db.add(plan)
        db.commit()
    finally:
        db.close()
    yield
    # 可选：清理数据库（为了测试之间隔离，可保留）
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)