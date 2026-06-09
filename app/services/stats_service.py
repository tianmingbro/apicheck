# app/services/stats_service.py
from sqlalchemy.orm import Session
from app.models.call_log import CallLog
from app.models.apikey import APIKey
from app.core.config import settings
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
    # 1. 写入调用日志
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
        error_message=error_message
    )
    db.add(log_entry)
    
    # 2. 更新 API Key 的统计信息和熔断计数
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).with_for_update().first()
    if api_key:
        api_key.total_calls += 1
        api_key.last_used_at = datetime.utcnow()
        
        if status_code >= 400:
            # 失败：递增 error_count
            api_key.error_count += 1
            # 检查是否达到阈值且当前是启用状态
            if api_key.is_enabled and api_key.error_count >= settings.KEY_FAILURE_THRESHOLD:
                api_key.is_enabled = False
                api_key.disabled_at = datetime.utcnow()
        else:
            # 成功：重置错误计数
            api_key.error_count = 0
            # 如果之前被禁用但恢复任务还未处理，这里不自动恢复（交给后台任务）
    
    db.commit()