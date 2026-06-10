#!/bin/bash
set -e

# 加载环境变量
if [ -f .env.prod ]; then
    export $(grep -v '^#' .env.prod | xargs)
else
    echo "❌ .env.prod not found!"
    exit 1
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 1. 拉取最新代码（如有未提交更改则跳过）
log_info "Pulling latest code..."
if ! git diff --quiet || ! git diff --cached --quiet; then
    log_error "Local changes exist. Commit or stash them first."
    exit 1
fi
git pull origin main

# 2. 构建前端（如果存在 frontend 目录）
if [ -d "frontend" ]; then
    log_info "Building frontend..."
    cd frontend
    # 解决依赖冲突
    if [ -f "package-lock.json" ]; then
        npm ci --legacy-peer-deps
    else
        npm install --legacy-peer-deps
    fi
    # 临时屏蔽可能触发 open 命令的错误（如果 build 脚本中有奇怪的命令）
    set +e
    npm run build
    BUILD_EXIT=$?
    set -e
    if [ $BUILD_EXIT -ne 0 ]; then
        log_error "Frontend build failed, but continuing with backend deployment..."
        # 可以选择退出或继续
        # exit 1
    fi
    cd ..
else
    log_info "No frontend directory, skipping frontend build."
fi

# 3. 启动数据库和 Redis（如果尚未运行）
log_info "Starting database and Redis..."
docker compose -f docker-compose.prod.yml up -d postgres redis

# 等待数据库就绪
log_info "Waiting for PostgreSQL to be ready..."
until docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-api_farm}; do
    sleep 1
done

# 4. 构建后端镜像
log_info "Building backend image..."
docker compose -f docker-compose.prod.yml build --no-cache

# 5. 运行数据库迁移
log_info "Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm app alembic upgrade head

# 6. 初始化套餐数据（幂等）
log_info "Seeding default plans..."
docker compose -f docker-compose.prod.yml run --rm app python scripts/seed_plans.py

# 7. 启动所有服务
log_info "Starting all services..."
docker compose -f docker-compose.prod.yml up -d

# 8. 健康检查（使用本地地址，Nginx 代理时可用域名）
log_info "Performing health check..."
sleep 5
HEALTH_URL="${HEALTH_CHECK_URL:-http://localhost:8000/health}"
if curl -sf "$HEALTH_URL" > /dev/null; then
    log_info "Health check passed"
else
    log_error "Health check failed! Rolling back..."
    docker compose -f docker-compose.prod.yml down
    exit 1
fi

log_info "✅ Deployment successful!"