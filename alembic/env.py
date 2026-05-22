"""
REFACTOR-A2.1 (2026-05-22) · Alembic env.py · 从 env var 读 DATABASE_URL
- 跟 db.py 同款(os.environ['DATABASE_URL'])· 单一数据源
- 支持 PEARNLY_DATABASE_URL override(给灰度期 / 多环境分离用)
- Supabase pooler 强制 sslmode=require
- 不用 SQLAlchemy ORM · target_metadata = None · 走 raw SQL(op.execute)

设计文档:docs/architecture/db-migration-plan.md §2.3
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def _resolve_database_url() -> str:
    """
    优先级:PEARNLY_DATABASE_URL > DATABASE_URL > alembic.ini sqlalchemy.url
    最后兜底 alembic.ini 的占位 · 让 alembic show / history 等无 DB 命令可跑
    """
    url = (
        os.environ.get("PEARNLY_DATABASE_URL", "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
    )
    if url:
        # Supabase pooler 默认要 sslmode=require · 跟 db.py 行为一致
        if "sslmode" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
        return url
    # 无 env var 时用 .ini 占位(只让无 DB 命令如 show head / history 可跑)
    return config.get_main_option("sqlalchemy.url") or "postgresql://localhost/_alembic_no_db"


def run_migrations_offline() -> None:
    """offline 模式:不连 DB · 只渲染 SQL · 用于 dry-run · alembic upgrade head --sql"""
    url = _resolve_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """online 模式:真连 DB · A2.2 后由 git-deploy.sh 钩子触发"""
    url = _resolve_database_url()
    if url.endswith("_alembic_no_db"):
        raise RuntimeError(
            "Alembic online 模式需要 PEARNLY_DATABASE_URL 或 DATABASE_URL 环境变量。"
            "本地跑请 set DATABASE_URL=postgresql://... 或用 offline 模式 "
            "(alembic upgrade head --sql)"
        )
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = url
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
