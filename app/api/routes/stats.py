"""Stats / usage API endpoint."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.call_log import CallLog
from app.schemas.stats import UsageStats, DailyBreakdown

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/usage", response_model=UsageStats)
def get_usage_stats(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to include in breakdown"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return usage statistics for the current user.

    Includes aggregate totals and a daily breakdown for charting.
    """
    user_id = current_user.id
    cutoff = datetime.utcnow() - timedelta(days=days)

    # ── Aggregate totals ──────────────────────────────────
    agg = (
        db.query(
            func.count(CallLog.id).label("total_calls"),
            func.coalesce(func.sum(CallLog.total_tokens), 0).label("total_tokens"),
        )
        .filter(CallLog.user_id == user_id)
        .first()
    )
    total_calls = agg.total_calls or 0
    total_tokens = agg.total_tokens or 0

    # ── Quota info ────────────────────────────────────────
    # Re-fetch user to get latest quota values
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    remaining = (user.quota_limit - user.quota_used) + user.extra_tokens

    # ── Daily breakdown ───────────────────────────────────
    rows = (
        db.query(
            cast(CallLog.created_at, Date).label("day"),
            func.count(CallLog.id).label("calls"),
            func.coalesce(func.sum(CallLog.total_tokens), 0).label("tokens"),
        )
        .filter(CallLog.user_id == user_id, CallLog.created_at >= cutoff)
        .group_by("day")
        .order_by("day")
        .all()
    )

    # Build a complete day range (fill gaps with zeros)
    daily: list[DailyBreakdown] = []
    cursor = cutoff.date()
    today = datetime.utcnow().date()
    row_map = {r.day: r for r in rows}
    while cursor <= today:
        r = row_map.get(cursor)
        daily.append(DailyBreakdown(
            date=cursor.isoformat(),
            calls=r.calls if r else 0,
            tokens=r.tokens if r else 0,
        ))
        cursor += timedelta(days=1)

    return UsageStats(
        total_calls=total_calls,
        total_tokens=total_tokens,
        quota_limit=user.quota_limit,
        quota_used=user.quota_used,
        extra_tokens=user.extra_tokens,
        remaining_quota=max(0, remaining),
        daily=daily,
    )
