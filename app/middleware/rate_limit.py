from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
import jwt
from app.core.config import settings
from app.utils.redis_client import sliding_window_rate_limit
import uuid

# 配置：需要限制的路由前缀及对应的限制参数
RATE_LIMIT_CONFIG = {
    "/chat/completions": {"limit": 10, "window": 60},      # 每分钟最多10次
    "/keys/": {"limit": 30, "window": 60},                 # 每分钟最多30次
    "/orders/create": {"limit": 5, "window": 60},          # 每分钟最多5次
}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 根据请求路径匹配限流配置（前缀匹配）
        path = request.url.path
        config = None
        for prefix, cfg in RATE_LIMIT_CONFIG.items():
            if path.startswith(prefix):
                config = cfg
                break
        
        if not config:
            return await call_next(request)
        
        # 获取用户标识：优先从 JWT 解析 user_id，否则使用 IP
        user_id = await self.get_user_id_from_token(request)
        identifier = f"user:{user_id}" if user_id else f"ip:{request.client.host}"
        
        # 构建 Redis key
        key = f"rate_limit:{identifier}:{path}"
        limit = config["limit"]
        window = config["window"]
        # 生成唯一成员（请求级别的随机标识）
        member = f"{uuid.uuid4()}"
        
        allowed, current_count, retry_after = await sliding_window_rate_limit(
            key, limit, window, member
        )
        
        # 添加响应头（即使未超限也加上，让客户端知道当前状态）
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(limit - current_count) if allowed else "0",
        }
        if not allowed:
            headers["Retry-After"] = str(retry_after)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests", "retry_after": retry_after},
                headers=headers
            )
        
        response = await call_next(request)
        # 在响应头中添加限制信息
        for k, v in headers.items():
            response.headers[k] = v
        return response
    
    async def get_user_id_from_token(self, request: Request) -> str | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            username = payload.get("sub")
            # 这里你可以从缓存或数据库查询 user_id，为了性能，直接返回 username
            # 如果 username 是唯一标识，也可以直接使用 username
            return username
        except jwt.PyJWTError:
            return None