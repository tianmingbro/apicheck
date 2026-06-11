"""Chat completions endpoint — proxy-aware, with proper error handling and logging."""
import logging
import uuid
import time
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import update
from datetime import datetime

from app.db.session import get_db, SessionLocal
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.apikey import APIKey
from app.models.call_log import CallLog
from app.core.load_balancer import LoadBalancer
from app.core.quota import check_and_deduct_quota, refund_quota
from app.utils.encryption import decrypt_api_key
from app.utils.http_client import create_http_client
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat completions"])


# ── Background log writer (independent session) ───────────
def _log_call_sync(
    request_id: str,
    user_id: int,
    api_key_id: int,
    model: str,
    status_code: int,
    duration_ms: int,
    error_msg: Optional[str],
    cost_cents: int,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Write call log in a separate DB session (runs as background task)."""
    db = SessionLocal()
    try:
        db.add(CallLog(
            request_id=request_id,
            user_id=user_id,
            api_key_id=api_key_id,
            model=model,
            status_code=status_code,
            duration_ms=duration_ms,
            error_message=error_msg,
            cost_cents=cost_cents,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            created_at=datetime.utcnow(),
        ))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to write call log (request_id=%s)", request_id)
    finally:
        db.close()


def _increment_error_count(api_key_id: int) -> None:
    """Increment the error_count of an API key in a separate session (fire-and-forget)."""
    db = SessionLocal()
    try:
        db.execute(
            update(APIKey)
            .where(APIKey.id == api_key_id)
            .values(error_count=APIKey.error_count + 1)
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to increment error_count for key_id=%d", api_key_id)
    finally:
        db.close()


# ── Main endpoint ─────────────────────────────────────────
@router.post("/completions", response_model=ChatResponse)
def chat_completions(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    estimated_cost = 1
    selected_key: Optional[APIKey] = None

    try:
        # ── 1. Load-balance select an API key ─────────────
        # Note: "least_used" is the default because round_robin requires
        # cross-request state (Redis) — new LoadBalancer instances reset the index.
        lb = LoadBalancer(db, strategy=settings.LOAD_BALANCER_STRATEGY)
        selected_key = lb.get_next_key(current_user.id)
        if not selected_key:
            raise HTTPException(status_code=503, detail="No available API key. Please add a valid key.")

        # ── 2. Quota check & deduct ───────────────────────
        if not check_and_deduct_quota(current_user.id, estimated_cost, db):
            raise HTTPException(status_code=402, detail="Insufficient quota. Please upgrade your plan.")

        # ── 3. Decrypt key, build upstream request ────────
        try:
            decrypted_key = decrypt_api_key(selected_key.key_value)
        except Exception:
            logger.exception("Failed to decrypt API key id=%d for user=%d", selected_key.id, current_user.id)
            raise HTTPException(status_code=500, detail="Failed to decrypt API key. Check your encryption configuration.")

        base_url = (selected_key.base_url or "https://api.openai.com/v1").rstrip("/")
        upstream_url = f"{base_url}/chat/completions"

        payload = request.model_dump(exclude_none=True)
        # Remove internal-only fields that OpenAI doesn't expect
        payload.pop("timeout", None)

        headers = {
            "Authorization": f"Bearer {decrypted_key}",
            "Content-Type": "application/json",
        }

        logger.info(
            "chat request_id=%s user=%s model=%s key_id=%d upstream=%s",
            request_id, current_user.username, request.model, selected_key.id, base_url,
        )

        # ── 4. Call upstream API ───────────────────────────
        upstream_data = None
        status_code = 500
        with create_http_client(timeout=120.0) as client:
            resp = client.post(upstream_url, json=payload, headers=headers)
            status_code = resp.status_code
            resp.raise_for_status()
            upstream_data = resp.json()

        # ── 5. Update API key statistics ──────────────────
        db.execute(
            update(APIKey)
            .where(APIKey.id == selected_key.id)
            .values(
                total_calls=APIKey.total_calls + 1,
                last_used_at=datetime.utcnow(),
                error_count=0,  # reset error count on success
            )
        )
        db.commit()

        # ── 6. Extract usage, schedule log ────────────────
        usage = upstream_data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        background_tasks.add_task(
            _log_call_sync,
            request_id, current_user.id, selected_key.id,
            request.model, status_code,
            int((time.time() - start_time) * 1000),
            None, estimated_cost, input_tokens, output_tokens,
        )

        logger.info(
            "chat success request_id=%s status=%d duration=%.0fms tokens=%d",
            request_id, status_code, (time.time() - start_time) * 1000,
            input_tokens + output_tokens,
        )

        return ChatResponse(
            id=upstream_data.get("id", request_id),
            object="chat.completion",
            created=upstream_data.get("created", int(time.time())),
            model=request.model,
            choices=upstream_data.get("choices", []),
            usage=usage,
        )

    except HTTPException:
        # Re-raise HTTPException as-is (already handled below for refund)
        raise

    except httpx.TimeoutException:
        logger.error("chat timeout request_id=%s upstream=%s after %.0fs",
                      request_id, getattr(selected_key, 'base_url', '?'),
                      time.time() - start_time)
        if selected_key:
            _increment_error_count(selected_key.id)
            refund_quota(current_user.id, estimated_cost, db)
        raise HTTPException(status_code=504, detail="Upstream API request timeout. Consider setting HTTPS_PROXY if you are in China.")

    except httpx.HTTPStatusError as e:
        logger.error("chat upstream error request_id=%s status=%d body=%s",
                      request_id, e.response.status_code,
                      (e.response.text or "")[:300])
        if selected_key:
            _increment_error_count(selected_key.id)
            refund_quota(current_user.id, estimated_cost, db)
        raise HTTPException(
            status_code=502,
            detail=f"Upstream API returned {e.response.status_code}: {(e.response.text or '')[:500]}",
        )

    except Exception:
        logger.exception("chat internal error request_id=%s user=%s", request_id, current_user.username)
        if selected_key:
            _increment_error_count(selected_key.id)
            refund_quota(current_user.id, estimated_cost, db)
        raise HTTPException(status_code=500, detail="Internal server error. Check server logs for details.")
