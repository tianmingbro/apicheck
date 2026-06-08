import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.base import Base

# Alembic 配置对象
config = context.config

# 如果存在日志配置文件，则使用
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 模型的元数据
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """离线模式运行迁移（不连接数据库）"""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """在线模式运行迁移（连接数据库）"""
    # 从 Alembic 配置中获取数据库 URL（我们动态覆盖）
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

# 根据环境选择运行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()