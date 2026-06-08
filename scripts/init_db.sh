#!/bin/bash
# scripts/init_db.sh - 一键初始化数据库

set -e  # 遇到错误立即退出

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Seeding default plans..."
python scripts/seed_plans.py

echo "==> Database initialization completed!"