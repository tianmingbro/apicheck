#!/bin/bash
# entrypoint.sh
set -e

# 等待数据库就绪
echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U ${POSTGRES_USER}; do
  sleep 1
done

# 运行 Alembic 迁移
echo "Running database migrations..."
alembic upgrade head

# 插入默认套餐（如果表为空）
echo "Seeding default plans..."
python scripts/seed_plans.py

# 启动主进程
exec "$@"