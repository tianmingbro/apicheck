# app/api/routes/chat.py
import uuid
import time
import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Dict, Any
import json
from datetime import datetime
from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.apikey import APIKey
from app.models.call_log import CallLog
from app.core.load_balancer import LoadBalancer
from app.core.quota import check_and_deduct_quota, refund_quota
from app.utils.encryption import decrypt_api_key
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat completions"])

# 全局 HTTP 客户端（连接池复用）
client = httpx.AsyncClient(timeout=60.0)

# 负载均衡器实例（策略可从配置读取）
lb = LoadBalancer(strategy="round_robin")

@router.post("/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    代理聊天请求：
    1. 检查配额
    2. 负载均衡选择一个可用的 API Key
    3. 转发请求到上游
    4. 记录调用日志（异步）
    5. 更新配额和 Key 使用统计
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # ---------- 1. 配额检查 ----------
    # 预估成本（可根据模型和 token 数计算，此处简化）
    estimated_cost = 1  # 单位：分（示例）
    if not await check_and_deduct_quota(current_user.id, estimated_cost, db):
        raise HTTPException(status_code=402, detail="Insufficient quota")
    
    # ---------- 2. 选择 API Key ----------
    selected_key = await lb.select_key(current_user.id, db)
    if not selected_key:
        raise HTTPException(status_code=503, detail="No available API Key")
    
    # 解密实际 Key 值
    decrypted_key = decrypt_api_key(selected_key.key_value)
    upstream_url = selected_key.base_url or "https://api.openai.com/v1/chat/completions"
    
    # ---------- 3. 转发请求到上游 ----------
    headers = {
        "Authorization": f"Bearer {decrypted_key}",
        "Content-Type": "application/json"
    }
    payload = request.dict(exclude_none=True)
    
    try:
        resp = await client.post(upstream_url, json=payload, headers=headers)
        resp.raise_for_status()
        upstream_data = resp.json()
        status_code = resp.status_code
        error_msg = None
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_msg = e.response.text
        upstream_data = None
    except Exception as e:
        await refund_quota(current_user.id, estimated_cost, db)
        raise HTTPException(status_code=500, detail=str(e))
    
    # ---------- 4. 记录调用日志（后台任务） ----------
    duration_ms = int((time.time() - start_time) * 1000)
    background_tasks.add_task(
        log_call,
        db, request_id, current_user.id, selected_key.id,
        request.model, status_code, duration_ms, error_msg,
        estimated_cost, input_tokens=0, output_tokens=0  # 实际可从响应提取
    )
    
    # ---------- 5. 更新 Key 使用统计 ----------
    await db.execute(
        update(APIKey)
        .where(APIKey.id == selected_key.id)
        .values(
            total_calls=APIKey.total_calls + 1,
            last_used_at=datetime.utcnow()
        )
    )
    await db.commit()
    
    # ---------- 6. 返回响应 ----------
    if error_msg:
        raise HTTPException(status_code=status_code, detail=error_msg)
    return ChatResponse(
        id=request_id,
        object="chat.completion",
        model=request.model,
        choices=upstream_data.get("choices", [])
    )

async def log_call(
    db: AsyncSession,
    request_id: str,
    user_id: int,
    api_key_id: int,
    model: str,
    status_code: int,
    duration_ms: int,
    error_msg: Optional[str],
    cost_cents: int,
    input_tokens: int,
    output_tokens: int
):
    
    """异步写入调用日志（由 background_tasks 执行）"""
    from app.db.session import async_session_factory  # 需在 session.py 中定义
    async with async_session_factory() as new_db:
        log = CallLog(
            request_id=request_id,
            user_id=user_id,
            api_key_id=api_key_id,
            model=model,
            status_code=status_code,
            duration_ms=duration_ms,
            error_message=error_msg,
            cost_cents=cost_cents,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens
        )
        new_db.add(log)
        await new_db.commit()