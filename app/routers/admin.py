# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User, UserRole
from app.models.apikey import APIKey
from app.models.call_log import CallLog
from app.models.plan import Plan
from app.schemas.admin import (
    UserResponse, UserUpdateRequest,
    APIKeyResponse, CallLogResponse,
    PlanCreateRequest, PlanUpdateRequest,
    LogsListResponse,PlanResponse
)

router = APIRouter(prefix="/admin", tags=["Admin"])

# ------------------- 用户管理 -------------------
@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if update_data.role:
        user.role = update_data.role
    if update_data.quota_limit is not None:
        user.quota_limit = update_data.quota_limit
    if update_data.extra_tokens is not None:
        user.extra_tokens = update_data.extra_tokens
    db.commit()
    return {"message": "User updated"}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

# ------------------- API Key 管理 -------------------
@router.get("/api-keys", response_model=List[APIKeyResponse])
def list_all_api_keys(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    query = db.query(APIKey)
    if user_id:
        query = query.filter(APIKey.user_id == user_id)
    keys = query.offset(skip).limit(limit).all()
    return keys

@router.post("/api-keys/{key_id}/toggle")
def toggle_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    key.is_enabled = not key.is_enabled
    db.commit()
    return {"is_enabled": key.is_enabled}

# ------------------- 日志审计 -------------------
@router.get("/logs", response_model=LogsListResponse)
def list_call_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = Query(None),
    model: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    order_by: str = Query("created_at", pattern="^(created_at|status_code|total_tokens|duration_ms)$"),
    order_desc: bool = Query(True),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    query = db.query(CallLog)
    
    # 筛选条件
    if user_id:
        query = query.filter(CallLog.user_id == user_id)
    if model:
        query = query.filter(CallLog.model == model)
    if status_code:
        query = query.filter(CallLog.status_code == status_code)
    if start_time:
        query = query.filter(CallLog.created_at >= start_time)
    if end_time:
        query = query.filter(CallLog.created_at <= end_time)
    
    # 排序
    order_column = getattr(CallLog, order_by)
    if order_desc:
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())
    
    # 分页
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return LogsListResponse(total=total, items=logs)

# ------------------- 套餐管理 -------------------
@router.get("/plans", response_model=List[PlanResponse])
def list_plans(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    return db.query(Plan).all()

@router.post("/plans", response_model=PlanResponse)
def create_plan(
    plan_data: PlanCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    new_plan = Plan(**plan_data.dict())
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan

@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    plan_data: PlanUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for key, value in plan_data.dict(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan

@router.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted"}