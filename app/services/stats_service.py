# app/services/stats_service.py
from sqlalchemy.orm import Session
from app.models.call_log import CallLog
from datetime import datetime

async def log_call(
    db: Session,
    request_id: str,
    user_id: int,
    api_key_id: int,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_tokens: int = 0,
    cost_cents: int = 0,
    status_code: int = 200,
    duration_ms: int = 0,
    error_message: str = None
):
    """记录调用日志到数据库（异步包装）"""
    log_entry = CallLog(
        request_id=request_id,
        user_id=user_id,
        api_key_id=api_key_id,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        cost_cents=cost_cents,
        status_code=status_code,
        duration_ms=duration_ms,
        error_message=error_message,
        created_at=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()  # 同步提交，但函数是 async 以兼容 await 调用