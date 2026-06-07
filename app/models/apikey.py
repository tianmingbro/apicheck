# app/models/apikey.py
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key_value: Mapped[str] = mapped_column(String(500), nullable=False)   # 加密存储
    base_url: Mapped[str] = mapped_column(String(200), nullable=True)     # 可选的上游地址
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    total_calls: Mapped[int] = mapped_column(Integer, default=0)

    # 关系（可选，方便联查）
    user = relationship("User", back_populates="api_keys")