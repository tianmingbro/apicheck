#!/bin/bash
set -e

# 1. 拉取最新代码
git pull origin main

# 2. 构建前端（假设前端单独构建）
cd frontend && npm ci && npm run build && cd ..

# 3. 构建后端镜像
docker compose -f docker-compose.prod.yml build

# 4. 运行数据库迁移
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# 5. 初始化套餐数据（如果为空）
docker compose -f docker-compose.prod.yml run --rm app python scripts/seed_plans.py

# 6. 启动所有服务
docker compose -f docker-compose.prod.yml up -d

# 7. 健康检查
sleep 5
curl -f https://your-domain.com/health || exit 1

echo "Deployment successful!"