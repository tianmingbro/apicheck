"""Circuit breaker tasks with Redis-based distributed locking.

Each gunicorn worker runs its own APScheduler instance.  Without locking
the same job would fire 4× concurrently.  We use Redis SET NX EX so only
one worker ever executes a given job at a time.
"""
import logging
import time
from datetime import datetime, timedelta

import redis as sync_redis

from app.db.session import SessionLocal
from app.models.apikey import APIKey
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Sync Redis client (one per process, lazily initialised) ──────────
_sync_redis: sync_redis.Redis | None = None


def _get_sync_redis() -> sync_redis.Redis:
    """Return a process-level sync Redis client."""
    global _sync_redis
    if _sync_redis is None:
        _sync_redis = sync_redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _sync_redis


def _acquire_lock(lock_name: str, ttl: int = 60) -> bool:
    """Try to acquire a Redis-backed distributed lock.

    Returns True if the lock was acquired (this worker should run the job).
    """
    try:
        r = _get_sync_redis()
        # SET key value NX EX ttl → returns True if key was set, None/False if it already exists
        return bool(r.set(f"lock:{lock_name}", str(time.time()), nx=True, ex=ttl))
    except Exception:
        logger.exception("Redis lock acquire failed for %s", lock_name)
        # On Redis error, fall back to executing the task (better than never running)
        return True


# ── Scheduled tasks ──────────────────────────────────────────────────
def disable_failed_keys():
    """Scan for keys with consecutive failures >= threshold and disable them.

    Runs every 5 minutes.  Only one worker executes thanks to Redis lock.
    """
    lock_name = "disable_failed_keys"
    if not _acquire_lock(lock_name, ttl=240):  # 4-min TTL < 5-min interval
        logger.debug("Skipping %s — another worker holds the lock", lock_name)
        return

    logger.info("Running %s", lock_name)
    db = SessionLocal()
    try:
        threshold = settings.KEY_FAILURE_THRESHOLD
        keys_to_disable = db.query(APIKey).filter(
            APIKey.is_enabled == True,
            APIKey.error_count >= threshold,
        ).all()

        for key in keys_to_disable:
            key.is_enabled = False
            key.disabled_at = datetime.utcnow()
            logger.warning(
                "Circuit-breaker: disabled key %d (user=%d, errors=%d)",
                key.id, key.user_id, key.error_count,
            )

        db.commit()
        if keys_to_disable:
            logger.info("disable_failed_keys: disabled %d key(s)", len(keys_to_disable))
        else:
            logger.debug("disable_failed_keys: no keys exceeded threshold")
    except Exception:
        logger.exception("Error in disable_failed_keys")
        db.rollback()
    finally:
        db.close()


def recover_disabled_keys():
    """Re-enable keys whose disable timeout has expired.

    Runs every KEY_RECOVERY_TIMEOUT_SECONDS seconds.
    """
    lock_name = "recover_disabled_keys"
    if not _acquire_lock(lock_name, ttl=max(30, settings.KEY_RECOVERY_TIMEOUT_SECONDS - 10)):
        logger.debug("Skipping %s — another worker holds the lock", lock_name)
        return

    logger.info("Running %s", lock_name)
    db = SessionLocal()
    try:
        timeout_seconds = settings.KEY_RECOVERY_TIMEOUT_SECONDS
        cutoff = datetime.utcnow() - timedelta(seconds=timeout_seconds)

        keys_to_recover = db.query(APIKey).filter(
            APIKey.is_enabled == False,
            APIKey.disabled_at.isnot(None),
            APIKey.disabled_at <= cutoff,
        ).all()

        for key in keys_to_recover:
            key.is_enabled = True
            key.disabled_at = None
            key.error_count = 0
            logger.info("Circuit-breaker: recovered key %d (user=%d)", key.id, key.user_id)

        db.commit()
        if keys_to_recover:
            logger.info("recover_disabled_keys: recovered %d key(s)", len(keys_to_recover))
        else:
            logger.debug("recover_disabled_keys: no keys ready for recovery")
    except Exception:
        logger.exception("Error in recover_disabled_keys")
        db.rollback()
    finally:
        db.close()
