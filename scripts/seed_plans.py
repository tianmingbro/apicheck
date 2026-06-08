#!/usr/bin/env python
# scripts/seed_plans.py
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.plan import Plan

def seed_plans():
    db = SessionLocal()
    try:
        # 检查是否已有数据，避免重复插入
        existing = db.query(Plan).first()
        if existing:
            print("Plans already exist, skipping seed.")
            return

        plans = [
            Plan(
                name="Free Plan",
                code="free",
                price_cents=0,
                currency="CNY",
                quota=1000,
                quota_unit="request",
                is_active=True,
                features={"rate_limit": "10/min", "support": "community"}
            ),
            Plan(
                name="Pro Plan",
                code="pro",
                price_cents=9900,  # 99元
                currency="CNY",
                quota=100000,
                quota_unit="request",
                is_active=True,
                features={"rate_limit": "100/min", "support": "email", "analytics": True}
            ),
            Plan(
                name="Enterprise Plan",
                code="enterprise",
                price_cents=49900,  # 499元
                currency="CNY",
                quota=1000000,
                quota_unit="request",
                is_active=True,
                features={"rate_limit": "500/min", "support": "24/7", "analytics": True, "sla": "99.9%"}
            )
        ]
        for plan in plans:
            db.add(plan)
        db.commit()
        print(f"Inserted {len(plans)} plans successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_plans()