# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "API Farm Commercial"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # 服务端配置
    HOST: str = Field("0.0.0.0", env="SERVER_HOST")
    PORT: int = Field(8000, env="SERVER_PORT")
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
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
    REDIS_URL: Optional[str] = Field("redis://localhost:6379/0", env="REDIS_URL")
    ENCRYPTION_KEY: Optional[str] = Field(None, env="ENCRYPTION_KEY")

    # 支付宝配置
    ALIPAY_APP_ID: str = Field(..., env="ALIPAY_APP_ID")
    ALIPAY_APP_PRIVATE_KEY: str = Field(..., env="ALIPAY_APP_PRIVATE_KEY")
    ALIPAY_PUBLIC_KEY: str = Field(..., env="ALIPAY_PUBLIC_KEY")
    ALIPAY_DEBUG: bool = Field(default=True, env="ALIPAY_DEBUG")  # True=沙箱环境
    ALIPAY_NOTIFY_URL: str = Field(..., env="ALIPAY_NOTIFY_URL")  # 异步回调地址
    ALIPAY_RETURN_URL: str = Field(..., env="ALIPAY_RETURN_URL")  # 同步跳转地址

    KEY_FAILURE_THRESHOLD: int = Field(5, env="KEY_FAILURE_THRESHOLD")          # 连续失败阈值
    KEY_RECOVERY_TIMEOUT_SECONDS: int = Field(300, env="KEY_RECOVERY_TIMEOUT_SECONDS")  # 恢复超时（秒）
    
    # ✅ Pydantic v2 配置方式
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",   # 忽略未定义的字段
    )

settings = Settings()