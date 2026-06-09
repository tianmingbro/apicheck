import pytest
import asyncio
import os
import time
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.apikey import APIKey
from app.models.call_log import CallLog
from app.models.plan import Plan
from app.models.order import Order
from app.utils.redis_client import init_redis, close_redis
from dotenv import load_dotenv
import os

# 加载项目根目录的 .env 文件（假设 pytest 在项目根目录运行）
load_dotenv()

# 可选：覆盖某些变量为测试专用值（避免使用真实支付宝密钥）
os.environ.setdefault("ALIPAY_APP_ID", "test_app_id")
os.environ.setdefault("ALIPAY_DEBUG", "true")

TEST_DATABASE_URL = "sqlite:///./test_e2e.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_env():
    # 创建表
    Base.metadata.create_all(bind=engine)
    settings.REDIS_URL = "redis://localhost:6379/1"
    # 使用 asyncio.run() 同步执行异步初始化
    asyncio.run(init_redis())
    # 创建管理员用户
    db = TestingSessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
    db.close()
    yield
    # 清理
    asyncio.run(close_redis())
    engine.dispose()
    time.sleep(0.2)  # 等待文件释放
    if os.path.exists("./test_e2e.db"):
        os.remove("./test_e2e.db")

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac