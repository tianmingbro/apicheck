from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis
from app.core.config import settings
from app.models.apikey import APIKey

class LoadBalancer:
    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.redis_client = redis.from_url(settings.REDIS_URL) if settings.REDIS_URL else None

    async def select_key(self, user_id: int, db: AsyncSession) -> APIKey:
        # 获取用户所有启用的 Key
        result = await db.execute(
            select(APIKey).where(
                APIKey.user_id == user_id,
                APIKey.is_enabled == True
            )
        )
        keys = result.scalars().all()
        if not keys:
            return None
        
        if self.strategy == "round_robin":
            # 从 Redis 获取当前索引（简化版：直接取第一个）
            # 生产环境需维护每个用户的轮询状态
            return keys[0]   # 后续可完善
        elif self.strategy == "least_used":
            return min(keys, key=lambda k: k.total_calls)
        else:
            return keys[0]