# app/utils/encryption.py
from cryptography.fernet import Fernet
from app.core.config import settings

def get_cipher() -> Fernet:
    """获取 Fernet 加密器（密钥从环境变量读取）"""
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError(
            "ENCRYPTION_KEY is not set in environment. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key)

def encrypt_api_key(value: str) -> str:
    """加密 API Key"""
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()

def decrypt_api_key(encrypted_value: str) -> str:
    """解密 API Key"""
    cipher = get_cipher()
    return cipher.decrypt(encrypted_value.encode()).decode()