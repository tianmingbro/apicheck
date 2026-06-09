# app/utils/redis_client.py
import time
import redis.asyncio as redis
from app.core.config import settings

redis_client: redis.Redis = None
_sliding_window_script = None

async def init_redis():
    """初始化 Redis 连接并注册 Lua 脚本"""
    global redis_client, _sliding_window_script
    # 注意：from_url 是异步方法，必须 await
    redis_client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20
    )
    # 测试连接是否成功
    await redis_client.ping()

    # 滑动窗口限流 Lua 脚本
    lua_code = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local member = ARGV[4]
        
        local start = now - window
        redis.call('ZREMRANGEBYSCORE', key, '-inf', start)
        local current_count = redis.call('ZCARD', key)
        if current_count < limit then
            redis.call('ZADD', key, now, member)
            redis.call('EXPIRE', key, window)
            return {1, current_count + 1, 0}
        else
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after = 0
            if oldest and #oldest >= 2 then
                retry_after = tonumber(oldest[2]) + window - now
                if retry_after < 0 then retry_after = 0 end
            end
            return {0, current_count, retry_after}
        end
    """
    _sliding_window_script = redis_client.register_script(lua_code)

async def close_redis():
    """关闭 Redis 连接"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

async def sliding_window_rate_limit(key: str, limit: int, window_seconds: int, member: str):
    """
    滑动窗口速率限制检查
    返回 (allowed: bool, current_count: int, retry_after: int)
    """
    if _sliding_window_script is None:
        raise RuntimeError("Redis client not initialized or Lua script not loaded")
    now = int(time.time())
    # 执行 Lua 脚本，返回 [allowed, count, retry_after]
    result = await _sliding_window_script(
        keys=[key],
        args=[now, window_seconds, limit, member]
    )
    allowed = (result[0] == 1)
    current_count = result[1]
    retry_after = result[2]
    return allowed, current_count, retry_after