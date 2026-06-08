# app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.routes import auth, keys, chat
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

# 创建 FastAPI 实例（不使用异步 lifespan）
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    redirect_slashes=False,
)

# 注册路由
app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(chat.router)

# 启动时同步创建表（开发环境，生产建议用 Alembic）
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("\n=== Registered Routes ===")
    for route in app.routes:
        print(f"{route.path} -> {list(route.methods) if hasattr(route, 'methods') else ''}")

# 关闭时释放数据库连接（可选）
@app.on_event("shutdown")
def shutdown():
    engine.dispose()

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}

# 请求日志中间件
class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Incoming request: {request.method} {request.url.path}")
        return await call_next(request)

app.add_middleware(LogMiddleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)