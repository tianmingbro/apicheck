# tests/test_quota.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.base import Base
from app.models.user import User
from app.core.quota import check_and_deduct_quota

# 异步 SQLite 内存数据库 URL
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def db_session():
    """创建异步数据库会话，每个测试独立"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_deduct_from_extra_tokens_first(db_session):
    user = User(username="test1", hashed_password="fake", role="user")
    user.quota_limit = 100
    user.quota_used = 0
    user.extra_tokens = 50
    db_session.add(user)
    await db_session.commit()
    
    result = await check_and_deduct_quota(user.id, 30, db_session)
    assert result is True
    await db_session.refresh(user)
    assert user.extra_tokens == 20
    assert user.quota_used == 0

@pytest.mark.asyncio
async def test_deduct_from_quota_when_extra_exhausted(db_session):
    user = User(username="test2", hashed_password="fake", role="user")
    user.quota_limit = 100
    user.quota_used = 0
    user.extra_tokens = 10
    db_session.add(user)
    await db_session.commit()
    
    result = await check_and_deduct_quota(user.id, 20, db_session)
    assert result is True
    await db_session.refresh(user)
    assert user.extra_tokens == 0
    assert user.quota_used == 10

@pytest.mark.asyncio
async def test_insufficient_quota(db_session):
    user = User(username="test3", hashed_password="fake", role="user")
    user.quota_limit = 100
    user.quota_used = 95
    user.extra_tokens = 0
    db_session.add(user)
    await db_session.commit()
    
    result = await check_and_deduct_quota(user.id, 10, db_session)
    assert result is False
    await db_session.refresh(user)
    assert user.quota_used == 95

@pytest.mark.asyncio
async def test_extra_tokens_sufficient_quota_exhausted(db_session):
    user = User(username="test4", hashed_password="fake", role="user")
    user.quota_limit = 100
    user.quota_used = 100
    user.extra_tokens = 50
    db_session.add(user)
    await db_session.commit()
    
    result = await check_and_deduct_quota(user.id, 30, db_session)
    assert result is True
    await db_session.refresh(user)
    assert user.extra_tokens == 20
    assert user.quota_used == 100

@pytest.mark.asyncio
async def test_quota_exhausted_and_no_extra(db_session):
    user = User(username="test5", hashed_password="fake", role="user")
    user.quota_limit = 100
    user.quota_used = 100
    user.extra_tokens = 0
    db_session.add(user)
    await db_session.commit()
    
    result = await check_and_deduct_quota(user.id, 1, db_session)
    assert result is False