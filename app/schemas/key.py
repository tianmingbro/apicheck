# app/schemas/key.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class APIKeyCreate(BaseModel):
    key_value: str
    base_url: Optional[str] = None

class APIKeyResponse(BaseModel):
    id: int
    key: str               # 脱敏后的 key（与原 SDK 期望的字段名一致）
    base_url: Optional[str]
    is_enabled: bool
    created_at: datetime
    total_calls: int
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True   # 允许从 ORM 对象转换

class APIKeyDeleteResponse(BaseModel):
    message: str