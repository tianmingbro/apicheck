import time
import pytest
from collections import deque

class InMemorySlidingWindow:
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.timestamps = deque()

    def allow(self, now=None):
        if now is None:
            now = time.time()
        # 清理窗口外的记录
        while self.timestamps and self.timestamps[0] <= now - self.window:
            self.timestamps.popleft()
        if len(self.timestamps) < self.limit:
            self.timestamps.append(now)
            return True, self.limit - len(self.timestamps), 0
        else:
            retry_after = int(self.timestamps[0] + self.window - now) + 1
            return False, 0, retry_after

def test_sliding_window_rate_limit_allow():
    limiter = InMemorySlidingWindow(limit=3, window=10)
    now = time.time()
    for i in range(3):
        allowed, remaining, _ = limiter.allow(now + i * 0.1)
        assert allowed is True
        assert remaining == 2 - i
    allowed, remaining, retry = limiter.allow(now + 0.5)
    assert allowed is False
    assert retry > 0

def test_sliding_window_rate_limit_window_expiry():
    limiter = InMemorySlidingWindow(limit=2, window=2)
    now = time.time()
    assert limiter.allow(now)[0] is True
    assert limiter.allow(now + 1)[0] is True
    # 窗口已过期，应允许新请求
    assert limiter.allow(now + 3)[0] is True