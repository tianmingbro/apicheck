# app/main.py
from fastapi import FastAPI
import httpx
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.routes import auth, keys, chat   # 导入 chat
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行：异步创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 2. 创建全局 httpx 客户端（复用连接池）
    app.state.httpx_client = httpx.AsyncClient(timeout=60.0)
    yield
    # 1. 关闭 httpx 客户端
    await app.state.httpx_client.aclose()
    # 关闭时执行：清理资源，例如关闭数据库引擎
    await engine.dispose()

# 创建 FastAPI 实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    redirect_slashes=False,
    lifespan=lifespan,  # 注册 lifespan 管理器
)
# 注册路由
app.include_router(auth.router)
app.include_router(keys.router)   # 新增
app.include_router(chat.router)   # 必须加上这一行
# @app.on_event("startup")
# def on_startup():
#     # 创建数据库表（仅开发用，生产环境应使用 Alembic）
#     # 注意：如果已经用 Alembic 管理，这行可以注释掉
#     Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "version": settings.APP_VERSION}

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}