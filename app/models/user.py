# app/models/user.py
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")  # "admin" or "user"

    # ===== 商业化字段 =====
    plan: Mapped[str] = mapped_column(String(50),nullable=False, server_default='free', default='free')          # free, pro, enterprise
    quota_limit: Mapped[int] = mapped_column(Integer, default=1000)        # 套餐总额度（按次或Token）
    quota_used: Mapped[int] = mapped_column(Integer, default=0)            # 已使用额度
    extra_tokens: Mapped[int] = mapped_column(Integer, default=0)          # 额外购买的点数
    subscription_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系（如果有 APIKey 模型）
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")