# app/models/apikey.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column,relationship
from datetime import datetime
from app.db.base import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key_value = Column(String(500), nullable=False)
    base_url = Column(String(200), nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    total_calls = Column(Integer, default=0)
    
    # 新增熔断相关字段
    error_count = Column(Integer, default=0)           # 连续失败次数
    disabled_at = Column(DateTime, nullable=True)      # 被熔断禁用的时间

    # 关系（可选，方便联查）
    user = relationship("User", back_populates="api_keys")

