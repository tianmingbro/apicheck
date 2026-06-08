# app/models/plan.py
from sqlalchemy import String, Integer, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="CNY")
    quota: Mapped[int] = mapped_column(Integer, nullable=False)
    quota_unit: Mapped[str] = mapped_column(String(20), default="request")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    features: Mapped[dict] = mapped_column(JSON, nullable=True)