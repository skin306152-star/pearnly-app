# -*- coding: utf-8 -*-
"""管家四表的 DDL 与首用自愈(sessions / messages / tasks / attachments)。

建表:alembic/versions/0088_steward_tables.py + 0089_steward_task_async.py +
0091_steward_attachments.py 逐字对齐留档,ensure_once 首用自愈(prod alembic 指针停 0020,
靠 ensure 补建,照 front_desk 先例)。

与 store.py 分家的理由是职责:这边只管「表长什么样、怎么建」,那边只管「怎么读写行」。
"""

from __future__ import annotations

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS steward_sessions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        user_id text NOT NULL,
        title text,
        created_at timestamptz NOT NULL DEFAULT now(),
        last_active_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS steward_tasks (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        session_id uuid REFERENCES steward_sessions (id) ON DELETE CASCADE,
        title text NOT NULL DEFAULT '',
        status text NOT NULL DEFAULT 'running',
        steps jsonb NOT NULL DEFAULT '[]'::jsonb,
        artifacts jsonb NOT NULL DEFAULT '[]'::jsonb,
        payload jsonb NOT NULL DEFAULT '{}'::jsonb,
        timeout_s integer NOT NULL DEFAULT 300,
        worker_id text,
        lease_until timestamptz,
        error_code text,
        error_message text,
        created_at timestamptz NOT NULL DEFAULT now(),
        finished_at timestamptz
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS steward_messages (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        session_id uuid NOT NULL REFERENCES steward_sessions (id) ON DELETE CASCADE,
        role text NOT NULL,
        text text NOT NULL DEFAULT '',
        tool_trace jsonb NOT NULL DEFAULT '[]'::jsonb,
        task_id uuid,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    # 会话附件(万能口):message_id 为空 = 还在附件盘里没送出;expires_at 到点由
    # attachments.sweep_expired 收(对话里扔的文件是临时件,不是业务档案)。
    """
    CREATE TABLE IF NOT EXISTS steward_attachments (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        session_id uuid NOT NULL REFERENCES steward_sessions (id) ON DELETE CASCADE,
        message_id uuid,
        user_id text NOT NULL,
        original_name text NOT NULL DEFAULT '',
        file_ref text NOT NULL DEFAULT '',
        size_bytes bigint NOT NULL DEFAULT 0,
        sha256 text NOT NULL DEFAULT '',
        mime text NOT NULL DEFAULT '',
        kind text NOT NULL DEFAULT 'unknown',
        kind_source text NOT NULL DEFAULT 'unknown',
        kind_reason text NOT NULL DEFAULT '',
        detect jsonb NOT NULL DEFAULT '{}'::jsonb,
        status text NOT NULL DEFAULT 'ready',
        promoted_to text,
        created_at timestamptz NOT NULL DEFAULT now(),
        expires_at timestamptz NOT NULL DEFAULT now() + interval '30 days'
    )
    """,
)

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_steward_sessions_tenant "
    "ON steward_sessions (tenant_id, last_active_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_steward_messages_session "
    "ON steward_messages (tenant_id, session_id, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_steward_tasks_session "
    "ON steward_tasks (tenant_id, session_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_steward_tasks_active "
    "ON steward_tasks (created_at) WHERE status = 'running'",
    "CREATE INDEX IF NOT EXISTS ix_steward_attachments_session "
    "ON steward_attachments (tenant_id, session_id, created_at)",
    "CREATE INDEX IF NOT EXISTS ix_steward_attachments_expiry "
    "ON steward_attachments (expires_at)",
)

# 0088 建的存量表补 0089 的列(新装由上面 CREATE 一步到位;两条路都幂等)。
_TASK_ALTERS = (
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS payload jsonb NOT NULL DEFAULT '{}'::jsonb",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS timeout_s integer NOT NULL DEFAULT 300",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS worker_id text",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS lease_until timestamptz",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS error_code text",
    "ALTER TABLE steward_tasks ADD COLUMN IF NOT EXISTS error_message text",
)

_RLS_TABLES = (
    "steward_sessions",
    "steward_tasks",
    "steward_messages",
    "steward_attachments",
)

_ensured = False


def ensure_tables() -> None:
    """幂等建四表 + 补列 + 索引 + tenant RLS(首用自愈)。独立事务,先于业务写事务调。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for ddl in _TASK_ALTERS:
            cur.execute(ddl)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)


def ensure_once() -> None:
    """进程内幂等包装(端点首用调,避免每请求 DDL)。"""
    global _ensured
    if _ensured:
        return
    ensure_tables()
    _ensured = True
