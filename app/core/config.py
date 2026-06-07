# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "API Farm Commercial"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # 服务端配置
    HOST: str = "0.0.0.0"          # 与原 .env 中的 HOST 对应
    PORT: int = 8000               # 与原 .env 中的 PORT 对应
    SERVER_HOST: str = "0.0.0.0"   # 备用
    SERVER_PORT: int = 8000        # 备用
    
    KEYPILOT_SERVER_URL: str = "http://localhost:8000"
    API_FARM_SERVER_URL: str = "http://localhost:8000"
    
    # 数据库配置
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # JWT 配置
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # 负载均衡及重试策略
    LOAD_BALANCER_STRATEGY: str = "round_robin"
    DEFAULT_TIMEOUT: int = 30
    MAX_RETRIES: int = 2
    
    # 免费层配额
    FREE_TIER_QUOTA: int = 1000
    
    # 日志级别
    LOG_LEVEL: str = "INFO"
    
    # 管理员初始账号（开发用）
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "ChangeMe123!"
    ADMIN_EMAIL: str = "admin@example.com"
    
    # Redis 配置（可选）
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")

    ENCRYPTION_KEY: Optional[str] = Field(None, env="ENCRYPTION_KEY")  # 用于加密 API Key，必须是 Fernet 生成的密钥
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True   # 保持大小写敏感，.env 中的键需要与字段名完全一致

settings = Settings()