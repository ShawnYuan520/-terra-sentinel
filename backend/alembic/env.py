"""Alembic 迁移环境配置"""
import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Alembic Config 对象
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# 导入所有模型（确保 Base.metadata 包含全部表）
import app.models  # noqa: F401
from app.core.database import Base
from app.core.config import get_settings

settings = get_settings()
target_metadata = Base.metadata


def run_migrations_offline():
    """离线模式 – 只生成 SQL 不连接数据库"""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """异步模式"""
    connectable = create_async_engine(settings.DATABASE_URL, echo=False)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    """在线模式"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()