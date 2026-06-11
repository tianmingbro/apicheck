# app/core/load_balancer.py
from sqlalchemy.orm import Session
from app.models.apikey import APIKey

class LoadBalancer:
    def __init__(self, db: Session, strategy: str = "round_robin"):
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
        elif self.strategy == "least_used":
            return min(keys, key=lambda k: k.total_calls)
        # 其他策略可扩展
        return keys[0]