"""Quota deduction and refund logic with transaction safety."""
import logging
from sqlalchemy.orm import Session
from app.models.user import User

logger = logging.getLogger(__name__)


def check_and_deduct_quota(user_id: int, cost: int, db: Session) -> bool:
    """Check and deduct quota for a user.

    Deducts from extra_tokens first, then from monthly quota.
    Returns True if deduction succeeded, False if insufficient quota.

    IMPORTANT: Caller must handle refund on upstream failure.
    """
    # Use with_for_update() to lock the row — requires an active transaction.
    # FastAPI's get_db yields a session with autocommit=False, so an implicit
    # transaction begins on the first query.
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user:
        logger.warning("check_and_deduct_quota: user %d not found", user_id)
        return False

    # 1) Consume extra_tokens first
    if user.extra_tokens >= cost:
        user.extra_tokens -= cost
        db.commit()
        logger.debug("user %d: deducted %d from extra_tokens (remaining=%d)", user_id, cost, user.extra_tokens)
        return True

    # 2) Fall back to monthly quota
    remaining = user.quota_limit - user.quota_used
    if remaining >= cost:
        user.quota_used += cost
        db.commit()
        logger.debug("user %d: deducted %d from quota (used=%d/%d)", user_id, cost, user.quota_used, user.quota_limit)
        return True

    logger.info("user %d: insufficient quota (need=%d, remaining=%d, extra=%d)",
                user_id, cost, remaining, user.extra_tokens)
    return False


def refund_quota(user_id: int, cost: int, db: Session) -> bool:
    """Refund quota after a failed upstream call.

    Tries to refund to quota_used first, then to extra_tokens.
    Never refunds more than was charged — best-effort safety.
    """
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user:
        logger.warning("refund_quota: user %d not found", user_id)
        return False

    # Try refunding from quota_used first (the common path for free-tier users)
    if user.quota_used >= cost:
        user.quota_used -= cost
        db.commit()
        logger.info("user %d: refunded %d to quota (used=%d/%d)", user_id, cost, user.quota_used, user.quota_limit)
        return True

    # Otherwise refund to extra_tokens
    user.extra_tokens += cost
    db.commit()
    logger.info("user %d: refunded %d to extra_tokens (now=%d)", user_id, cost, user.extra_tokens)
    return True
