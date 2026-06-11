#!/usr/bin/env python3
"""Initialize database: create tables and seed default admin user + plans."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.user import User
from app.models.plan import Plan
from app.models.order import Order  # needed for User.orders relationship resolution


def init_db():
    """Create all tables and seed initial data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

    db = SessionLocal()
    try:
        # Seed admin user if not exists
        existing_admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not existing_admin:
            admin = User(
                username=settings.ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role="admin",
                quota_limit=999999,
            )
            db.add(admin)
            print(f"✓ Admin user '{settings.ADMIN_USERNAME}' created")
        else:
            print(f"✓ Admin user '{settings.ADMIN_USERNAME}' already exists")

        # Seed plans if not exists
        existing_plans = db.query(Plan).first()
        if not existing_plans:
            plans = [
                Plan(
                    name="Free Plan",
                    code="free",
                    price_cents=0,
                    currency="CNY",
                    quota=1000,
                    quota_unit="request",
                    is_active=True,
                    features={"rate_limit": "10次/分钟", "support": "社区支持"},
                ),
                Plan(
                    name="Pro Plan",
                    code="pro",
                    price_cents=9900,
                    currency="CNY",
                    quota=100000,
                    quota_unit="request",
                    is_active=True,
                    features={
                        "rate_limit": "100次/分钟",
                        "support": "邮件支持",
                        "analytics": True,
                    },
                ),
                Plan(
                    name="Enterprise Plan",
                    code="enterprise",
                    price_cents=49900,
                    currency="CNY",
                    quota=1000000,
                    quota_unit="request",
                    is_active=True,
                    features={
                        "rate_limit": "500次/分钟",
                        "support": "7×24小时",
                        "analytics": True,
                        "sla": True,
                    },
                ),
            ]
            for plan in plans:
                db.add(plan)
            print(f"✓ {len(plans)} plans seeded")
        else:
            print("✓ Plans already seeded")

        db.commit()
        print("✓ Database initialized successfully")
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
