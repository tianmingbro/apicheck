# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.api.routes import auth, chat
from app.api.routes import keys
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.routers import orders
from app.utils.redis_client import init_redis, close_redis
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.admin_auth import AdminAuthMiddleware
from app.tasks.circuit_breaker import disable_failed_keys, recover_disabled_keys
from app.routers import admin

# 创建全局调度器实例
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化 Redis 连接池
    await init_redis()
    print("Redis connected")
    # 创建数据库表（同步操作）
    Base.metadata.create_all(bind=engine)
    print("Database tables created")

    # 启动后台定时任务
    # 每 5 分钟执行一次禁用扫描
    scheduler.add_job(disable_failed_keys, 'interval', minutes=5, id='disable_failed_keys')
    # 每 KEY_RECOVERY_TIMEOUT_SECONDS 秒执行一次恢复扫描
    scheduler.add_job(
        recover_disabled_keys,
        'interval',
        seconds=settings.KEY_RECOVERY_TIMEOUT_SECONDS,
        id='recover_disabled_keys'
    )
    scheduler.start()
    print("Scheduler started")

    yield

    # 关闭时：停止调度器，释放 Redis 连接
    scheduler.shutdown()
    print("Scheduler shut down")
    await close_redis()
    print("Redis disconnected")
    engine.dispose()
    print("Database engine disposed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    redirect_slashes=False,
    lifespan=lifespan,
)

# 注册路由
app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(chat.router)
app.include_router(orders.router)
app.include_router(admin.router)

# 添加请求日志中间件（建议放在最外层，用于记录所有请求）
class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Incoming request: {request.method} {request.url.path}")
        response = await call_next(request)
        print(f"Response status: {response.status_code}")
        return response


app.add_middleware(LogMiddleware)

# 添加速率限制中间件（在日志之后，业务之前）
app.add_middleware(RateLimitMiddleware)

app.add_middleware(AdminAuthMiddleware)

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )