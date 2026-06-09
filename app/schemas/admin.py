# app/schemas/admin.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
from typing import List
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
from unittest.mock import AsyncMock

# 在导入 app 之前 mock redis 模块
sys.modules['app.utils.redis_client'] = AsyncMock()
sys.modules['app.utils.redis_client'].init_redis = AsyncMock()
sys.modules['app.utils.redis_client'].close_redis = AsyncMock()

class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    quota_limit: int
    quota_used: int
    extra_tokens: int
    created_at: datetime
    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    quota_limit: Optional[int] = None
    extra_tokens: Optional[int] = None

class APIKeyResponse(BaseModel):
    id: int
    user_id: int
    key_value: str   # 注意：管理员能看到加密值？应该解密后展示？实际可使用脱敏
    is_enabled: bool
    total_calls: int
    last_used_at: Optional[datetime]
    class Config:
        from_attributes = True

class CallLogResponse(BaseModel):
    id: int
    request_id: str
    user_id: int
    api_key_id: Optional[int]
    model: str
    total_tokens: int
    status_code: int
    duration_ms: int
    error_message: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class PlanCreateRequest(BaseModel):
    name: str
    code: str
    price_cents: int
    currency: str = "CNY"
    quota: int
    quota_unit: str = "request"
    is_active: bool = True
    features: dict = {}

class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    price_cents: Optional[int] = None
    quota: Optional[int] = None
    is_active: Optional[bool] = None
    features: Optional[dict] = None

class LogsListResponse(BaseModel):
    total: int
    items: List[CallLogResponse]

class PlanResponse(BaseModel):
    id: int
    name: str
    code: str
    price_cents: int
    currency: str
    quota: int
    quota_unit: str
    is_active: bool
    features: Optional[Dict[str, Any]] = None
    class Config:
        from_attributes = True