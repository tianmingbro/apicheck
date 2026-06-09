# app/tasks/circuit_breaker.py
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.apikey import APIKey
from app.core.config import settings

logger = logging.getLogger(__name__)

def disable_failed_keys():
    """
    将连续失败次数超过阈值的 key 禁用（熔断）
    运行频率：每 5 分钟
    """
    db = SessionLocal()
    try:
        threshold = settings.KEY_FAILURE_THRESHOLD
        # 查找 is_enabled=True 且 error_count >= threshold 的 key
        keys_to_disable = db.query(APIKey).filter(
            APIKey.is_enabled == True,
            APIKey.error_count >= threshold
        ).all()
        
        for key in keys_to_disable:
            key.is_enabled = False
            key.disabled_at = datetime.utcnow()
            logger.warning(f"API Key {key.id} (user {key.user_id}) disabled due to {key.error_count} consecutive failures")
        
        db.commit()
        if keys_to_disable:
            logger.info(f"Disabled {len(keys_to_disable)} API keys")
    except Exception as e:
        logger.exception("Error in disable_failed_keys task")
        db.rollback()
    finally:
        db.close()

def recover_disabled_keys():
    """
    恢复已过禁用期的 key（重新启用，重置错误计数）
    运行频率：每 300 秒（可配置）
    """
    db = SessionLocal()
    try:
        timeout_seconds = settings.KEY_RECOVERY_TIMEOUT_SECONDS
        recovery_cutoff = datetime.utcnow() - timedelta(seconds=timeout_seconds)
        
        keys_to_recover = db.query(APIKey).filter(
            APIKey.is_enabled == False,
            APIKey.disabled_at != None,
            APIKey.disabled_at <= recovery_cutoff
        ).all()
        
        for key in keys_to_recover:
            key.is_enabled = True
            key.disabled_at = None
            key.error_count = 0   # 重置计数
            logger.info(f"API Key {key.id} (user {key.user_id}) recovered after {timeout_seconds}s")
        
        db.commit()
        if keys_to_recover:
            logger.info(f"Recovered {len(keys_to_recover)} API keys")
    except Exception as e:
        logger.exception("Error in recover_disabled_keys task")
        db.rollback()
    finally:
        db.close()