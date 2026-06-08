# app/core/quota.py
from sqlalchemy.orm import Session
from app.models.user import User

def check_and_deduct_quota(user_id: int, cost: int, db: Session) -> bool:
    """检查并扣减用户配额，返回是否成功"""
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user:
        return False
    if user.extra_tokens >= cost:
        user.extra_tokens -= cost
        db.commit()
        return True
    remaining = user.quota_limit - user.quota_used
    if remaining >= cost:
        user.quota_used += cost
        db.commit()
        return True
    return False

def refund_quota(user_id: int, cost: int, db: Session) -> bool:
    """退还配额（用于错误回滚），简单实现，直接增加已用配额回退"""
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user:
        return False
    # 如果之前从套餐配额扣减，则退还；如果从 extra_tokens 扣减，退还 extra_tokens
    # 这里简化：优先退还给 extra_tokens 逻辑较复杂，暂只支持退套餐配额
    if user.quota_used >= cost:
        user.quota_used -= cost
        db.commit()
        return True
    return False