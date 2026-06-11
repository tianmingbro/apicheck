"""Stats / usage schemas."""
from pydantic import BaseModel
from typing import List


class DailyBreakdown(BaseModel):
    date: str
    calls: int
    tokens: int


class UsageStats(BaseModel):
    total_calls: int
    total_tokens: int
    quota_limit: int
    quota_used: int
    extra_tokens: int
    remaining_quota: int
    daily: List[DailyBreakdown]
