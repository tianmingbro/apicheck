# app/middleware/admin_auth.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import jwt
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User, UserRole

class AdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 只拦截 /admin 开头的路径
        if request.url.path.startswith("/admin"):
            # 获取 Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return Response("Unauthorized", status_code=401)
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                username = payload.get("sub")
                if not username:
                    return Response("Invalid token", status_code=401)
                # 查询用户角色
                db = SessionLocal()
                user = db.query(User).filter(User.username == username).first()
                db.close()
                if not user or user.role != UserRole.ADMIN:
                    return Response("Forbidden", status_code=403)
                # 将用户信息存入 request.state 供后续使用
                request.state.admin_user = user
            except jwt.PyJWTError:
                return Response("Invalid token", status_code=401)
        return await call_next(request)