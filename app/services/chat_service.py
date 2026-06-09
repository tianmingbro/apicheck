import httpx
import uuid
import time
from typing import Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.apikey import APIKey
from app.models.call_log import CallLog
from app.core.load_balancer import LoadBalancer
from app.core.quota import check_and_deduct_quota
from app.utils.encryption import decrypt_api_key

# 全局 HTTP 客户端
# client = httpx.AsyncClient(timeout=120.0)
# 全局 HTTP 客户端（可替换）
_default_client = httpx.AsyncClient(timeout=120.0)

def _get_client():
    return _default_client

def _set_client(client):
    global _default_client
    _default_client = client

async def log_call(db: Session, request_id: str, user_id: int, api_key_id: int,
                   model: str, input_tokens: int, output_tokens: int, total_tokens: int,
                   cost_cents: int, status_code: int, duration_ms: int, error_message: str = None):
    """内联日志记录函数，避免导入依赖"""
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
    db.commit()

class ChatService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.user = current_user
        self.lb = LoadBalancer(db, strategy="round_robin")

    async def process_chat_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        api_key_entry = self.lb.get_next_key(self.user.id)
        if not api_key_entry:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No available API keys found. Please add a valid key."
            )

        if not check_and_deduct_quota(self.user.id, 1, self.db):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient quota. Please upgrade your plan."
            )

        start_time = time.time()
        request_id = str(uuid.uuid4())
        decrypted_key = decrypt_api_key(api_key_entry.key_value)
        upstream_url = api_key_entry.base_url or "https://api.openai.com/v1"
        headers = {"Authorization": f"Bearer {decrypted_key}", "Content-Type": "application/json"}
        url = f"{upstream_url}/chat/completions"

        try:
            response = await _get_client().post(url, json=request_data, headers=headers)
            duration_ms = int((time.time() - start_time) * 1000)
            response_data = response.json()
            response.raise_for_status()

            await log_call(
                db=self.db, request_id=request_id, user_id=self.user.id,
                api_key_id=api_key_entry.id, model=request_data.get("model"),
                input_tokens=response_data.get("usage", {}).get("prompt_tokens", 0),
                output_tokens=response_data.get("usage", {}).get("completion_tokens", 0),
                total_tokens=response_data.get("usage", {}).get("total_tokens", 0),
                cost_cents=0, status_code=response.status_code, duration_ms=duration_ms
            )
            return response_data

        except httpx.TimeoutException:
            duration_ms = int((time.time() - start_time) * 1000)
            await log_call(
                db=self.db, request_id=request_id, user_id=self.user.id,
                api_key_id=api_key_entry.id, model=request_data.get("model"),
                input_tokens=0, output_tokens=0, total_tokens=0, cost_cents=0,
                status_code=status.HTTP_504_GATEWAY_TIMEOUT, duration_ms=duration_ms,
                error_message="Upstream timeout"
            )
            raise HTTPException(status_code=504, detail="Upstream API request timeout")

        except httpx.HTTPStatusError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            await log_call(
                db=self.db, request_id=request_id, user_id=self.user.id,
                api_key_id=api_key_entry.id, model=request_data.get("model"),
                input_tokens=0, output_tokens=0, total_tokens=0, cost_cents=0,
                status_code=e.response.status_code, duration_ms=duration_ms,
                error_message=f"Upstream API error: {e.response.text}"
            )
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            await log_call(
                db=self.db, request_id=request_id, user_id=self.user.id,
                api_key_id=api_key_entry.id, model=request_data.get("model"),
                input_tokens=0, output_tokens=0, total_tokens=0, cost_cents=0,
                status_code=500, duration_ms=duration_ms, error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")