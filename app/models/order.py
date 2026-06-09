# app/models/order.py
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class OrderStatus(str, PyEnum):
    PENDING = "pending"      # 待支付
    PAID = "paid"            # 已支付
    CANCELLED = "cancelled"  # 已取消
    EXPIRED = "expired"      # 已过期

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)          # 金额（分）
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    trade_no = Column(String(64), unique=True, nullable=False, index=True)  # 商户订单号
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系（可选）
    user = relationship("User", back_populates="orders")
    plan = relationship("Plan")