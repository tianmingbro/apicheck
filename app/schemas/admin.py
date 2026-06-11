"""Admin-related Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.user import UserRole


# ── User ──────────────────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    quota_limit: int
    quota_used: int
    extra_tokens: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    role: Optional[str] = None
    quota_limit: Optional[int] = None
    extra_tokens: Optional[int] = None


# ── API Key ───────────────────────────────────────────────
class APIKeyResponse(BaseModel):
    id: int
    user_id: int
    key_value: str  # encrypted; decrypt + mask before returning
    is_enabled: bool
    total_calls: int
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Call Log ──────────────────────────────────────────────
class CallLogResponse(BaseModel):
    id: int
    request_id: str
    user_id: int
    api_key_id: Optional[int] = None
    model: str
    total_tokens: int
    status_code: int
    duration_ms: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LogsListResponse(BaseModel):
    total: int
    items: List[CallLogResponse]


# ── Plan ──────────────────────────────────────────────────
class PlanCreateRequest(BaseModel):
    name: str
    code: str
    price_cents: int
    currency: str = "CNY"
    quota: int
    quota_unit: str = "request"
    is_active: bool = True
    features: Optional[Dict[str, Any]] = None


class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    price_cents: Optional[int] = None
    quota: Optional[int] = None
    is_active: Optional[bool] = None
    features: Optional[Dict[str, Any]] = None


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
