# app/api/routes/keys.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.apikey import APIKey
from app.schemas.key import APIKeyCreate, APIKeyResponse, APIKeyDeleteResponse
from app.utils.encryption import encrypt_api_key, decrypt_api_key

router = APIRouter(prefix="/keys", tags=["api keys"])

def mask_api_key(key_value: str) -> str:
    """脱敏显示：保留前4位和后4位"""
    if len(key_value) <= 8:
        return "*" * len(key_value)
    return key_value[:4] + "*" * (len(key_value) - 8) + key_value[-4:]

@router.get("/", response_model=List[APIKeyResponse])
def list_keys(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    result = []
    for key in keys:
        decrypted = decrypt_api_key(key.key_value)
        result.append(APIKeyResponse(
            id=key.id,
            key=mask_api_key(decrypted),
            base_url=key.base_url,
            is_enabled=key.is_enabled,
            created_at=key.created_at,
            total_calls=key.total_calls,
            last_used_at=key.last_used_at
        ))
    return result

@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """添加新的 API Key（加密存储）"""
    encrypted_value = encrypt_api_key(key_data.key_value)
    new_key = APIKey(
        user_id=current_user.id,
        key_value=encrypted_value,
        base_url=key_data.base_url,
        is_enabled=True
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return APIKeyResponse(
        id=new_key.id,
        key=mask_api_key(key_data.key_value),
        base_url=new_key.base_url,
        is_enabled=new_key.is_enabled,
        created_at=new_key.created_at,
        total_calls=new_key.total_calls,
        last_used_at=new_key.last_used_at
    )

@router.delete("/{key_id}", response_model=APIKeyDeleteResponse)
async def delete_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除指定的 API Key（只能删除自己的）"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    await db.delete(key)
    await db.commit()
    return APIKeyDeleteResponse(message="API Key deleted successfully")