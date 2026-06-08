# app/core/load_balancer.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.apikey import APIKey

class LoadBalancer:
    def __init__(self, db: AsyncSession, strategy: str = "round_robin"):
        self.db = db
        self.strategy = strategy
        self._index = 0   # 关键：轮询计数器

    def get_next_key(self, user_id: int):
        keys = self.db.query(APIKey).filter(APIKey.user_id == user_id, APIKey.is_enabled == True).all()
        if not keys:
            return None

        if self.strategy == "round_robin":
            idx = self._index % len(keys)
            selected = keys[idx]
            self._index += 1
            return selected
        # 其他策略可扩展
        return keys[0]