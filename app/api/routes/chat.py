import uuid
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import update
from datetime import datetime
import httpx

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.apikey import APIKey
from app.models.call_log import CallLog
from app.core.load_balancer import LoadBalancer
from app.core.quota import check_and_deduct_quota
from app.utils.encryption import decrypt_api_key
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat completions"])

def log_call_sync(
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
    """同步记录日志（使用独立数据库会话）"""
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        log_entry = CallLog(
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
            total_tokens=input_tokens + output_tokens,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@router.post("/completions", response_model=ChatResponse)
def chat_completions(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    estimated_cost = 1

    # 1. 负载均衡选择 API Key
    lb = LoadBalancer(db, strategy="round_robin")
    selected_key = lb.get_next_key(current_user.id)
    if not selected_key:
        raise HTTPException(status_code=503, detail="No available API key")

    # 2. 配额检查（在转发之前扣费）
    if not check_and_deduct_quota(current_user.id, estimated_cost, db):
        raise HTTPException(status_code=402, detail="Insufficient quota")

    decrypted_key = decrypt_api_key(selected_key.key_value)
    upstream_url = selected_key.base_url or "https://api.openai.com/v1/chat/completions"

    headers = {"Authorization": f"Bearer {decrypted_key}", "Content-Type": "application/json"}
    payload = request.model_dump(exclude_none=True)  # 使用 model_dump 替代 dict
    upstream_data = None
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(upstream_url, json=payload, headers=headers)
            resp.raise_for_status()
            upstream_data = resp.json()
            status_code = resp.status_code
    except httpx.TimeoutException:
        # 超时：配额已扣，暂不退还（后续可优化）
        raise HTTPException(status_code=504, detail="Upstream API request timeout")
    except httpx.HTTPStatusError as e:
        detail = e.response.text if e.response.text else str(e)
        raise HTTPException(status_code=e.response.status_code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if upstream_data is None:
        raise HTTPException(status_code=500, detail="Internal error: upstream data missing")
    # 3. 更新 API Key 统计
    db.execute(
        update(APIKey)
        .where(APIKey.id == selected_key.id)
        .values(
            total_calls=APIKey.total_calls + 1,
            last_used_at=datetime.utcnow()
        )
    )
    db.commit()

    # 4. 提取用量
    usage = upstream_data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)

    # 5. 异步记录日志（使用独立会话）
    background_tasks.add_task(
        log_call_sync,
        request_id,
        current_user.id,
        selected_key.id,
        request.model,
        status_code,
        int((time.time() - start_time) * 1000),
        None,
        estimated_cost,
        input_tokens,
        output_tokens
    )

    return ChatResponse(
        id=upstream_data.get("id", request_id),
        object="chat.completion",
        created=upstream_data.get("created", int(time.time())),
        model=request.model,
        choices=upstream_data.get("choices", []),
        usage=usage
    )