# app/main.py
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.utils.logger import setup_logging
from app.utils.redis_client import init_redis, close_redis
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.admin_auth import AdminAuthMiddleware
from app.tasks.circuit_breaker import disable_failed_keys, recover_disabled_keys

# ── Logging ──────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

# ── Scheduler (one per process, not per worker) ──────────
_scheduler: BackgroundScheduler | None = None


def _get_scheduler() -> BackgroundScheduler:
    """Return a process-level singleton scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


# ── Lifespan (should only create tables / scheduler once per process) ──
_startup_done = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _startup_done

    # Only do heavyweight init once per gunicorn worker process
    if not _startup_done:
        _startup_done = True
        await init_redis()
        logger.info("Redis connected")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified")

        scheduler = _get_scheduler()
        scheduler.add_job(disable_failed_keys, 'interval', minutes=5, id='disable_failed_keys')
        scheduler.add_job(
            recover_disabled_keys,
            'interval',
            seconds=settings.KEY_RECOVERY_TIMEOUT_SECONDS,
            id='recover_disabled_keys',
        )
        scheduler.start()
        logger.info("Background scheduler started (interval tasks)")
    else:
        logger.info("Startup already done in this process, skipping init")

    yield

    # Shutdown: only the "owning" concept doesn't apply cleanly with gunicorn,
    # but each process shuts down its own scheduler on exit.
    scheduler = _get_scheduler()
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down")
    await close_redis()
    logger.info("Redis disconnected")
    engine.dispose()
    logger.info("Database engine disposed")


# ── App ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    redirect_slashes=False,
    lifespan=lifespan,
)

# Import routers AFTER app creation to avoid circular imports
from app.api.routes import auth, chat, keys, stats  # noqa: E402
from app.routers import orders, admin  # noqa: E402

app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(chat.router)
app.include_router(stats.router)
app.include_router(orders.orders_router)
app.include_router(orders.plans_router)
app.include_router(admin.router)


# ── Global exception handler ─────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log full traceback for unhandled exceptions before returning 500."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please check server logs."},
    )


# ── Request logging middleware ───────────────────────────
class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info("→ %s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("← %s %s → %d", request.method, request.url.path, response.status_code)
        return response


app.add_middleware(LogMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AdminAuthMiddleware)

# ── CORS middleware (added last = applied first for responses) ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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