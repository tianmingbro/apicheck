import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select   # 添加这一行
from app.db.base import Base
from app.models.user import User
from app.models.apikey import APIKey
from app.core.load_balancer import LoadBalancer

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_round_robin_selection(db_session):
    user = User(username="lbuser", hashed_password="fake", role="user")
    db_session.add(user)
    await db_session.commit()

    keys = []
    for i in range(3):
        key = APIKey(user_id=user.id, key_value=f"encrypted_key_{i}", is_enabled=True)
        db_session.add(key)
        keys.append(key)
    await db_session.commit()

    # 可选：调试确认数据库内容
    result = await db_session.execute(select(APIKey))
    all_keys = result.scalars().all()
    print("Keys in DB:", [(k.id, k.user_id, k.is_enabled) for k in all_keys])

    lb = LoadBalancer(db_session, strategy="round_robin")

    selected_ids = []
    for _ in range(6):
        key = await lb.get_next_key(user.id)
        selected_ids.append(key.id)

    expected = [keys[0].id, keys[1].id, keys[2].id,
                keys[0].id, keys[1].id, keys[2].id]
    assert selected_ids == expected

@pytest.mark.asyncio
async def test_skip_disabled_keys(db_session):
    user = User(username="lbuser2", hashed_password="fake", role="user")
    db_session.add(user)
    await db_session.commit()

    key1 = APIKey(user_id=user.id, key_value="k1", is_enabled=True)
    key2 = APIKey(user_id=user.id, key_value="k2", is_enabled=False)
    key3 = APIKey(user_id=user.id, key_value="k3", is_enabled=True)
    db_session.add(key1)
    db_session.add(key2)
    db_session.add(key3)
    await db_session.commit()

    lb = LoadBalancer(db_session, strategy="round_robin")

    selected = []
    for _ in range(4):
        key = await lb.get_next_key(user.id)
        selected.append(key.id)

    assert selected == [key1.id, key3.id, key1.id, key3.id]

@pytest.mark.asyncio
async def test_no_available_key(db_session):
    user = User(username="lbuser3", hashed_password="fake", role="user")
    db_session.add(user)
    await db_session.commit()

    lb = LoadBalancer(db_session, strategy="round_robin")
    key = await lb.get_next_key(user.id)
    assert key is None

@pytest.mark.asyncio
async def test_all_keys_disabled(db_session):
    user = User(username="lbuser4", hashed_password="fake", role="user")
    db_session.add(user)
    await db_session.commit()

    key = APIKey(user_id=user.id, key_value="k1", is_enabled=False)
    db_session.add(key)
    await db_session.commit()

    lb = LoadBalancer(db_session, strategy="round_robin")
    result = await lb.get_next_key(user.id)
    assert result is None