# -*- coding: utf-8 -*-
"""DMS LINE 表结构 + 多 OA 迁移(幂等自愈)。

prod 无 alembic 钩子:首用 `ensure_tables` 幂等建表/迁移 + `_with_heal` 重试一次。迁移含
DROP/ADD 约束,多实例并发首用会互相打架 → 先取事务级 advisory lock(Postgres 分布式锁,
不是单机文件锁)串行化。alembic 0125_dms_multi_line_oa 是同一份 DDL 的发布记录。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_BINDINGS = """
CREATE TABLE IF NOT EXISTS line_dms_bindings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    line_user_id text,
    channel_key text NOT NULL DEFAULT 'dms',
    tenant_id uuid NOT NULL,
    user_id uuid NOT NULL,
    display_name text,
    bound_at timestamptz DEFAULT now(),
    last_active_at timestamptz
)
"""

_BINDING_CODES = """
CREATE TABLE IF NOT EXISTS line_dms_binding_codes (
    code text PRIMARY KEY,
    channel_key text NOT NULL DEFAULT 'dms',
    tenant_id uuid,
    user_id uuid,
    expires_at timestamptz,
    used_at timestamptz
)
"""

_SESSIONS = """
CREATE TABLE IF NOT EXISTS dms_line_sessions (
    tenant_id uuid NOT NULL,
    channel_key text NOT NULL DEFAULT 'dms',
    line_user_id text NOT NULL,
    state text,
    payload jsonb DEFAULT '{}',
    expires_at timestamptz NOT NULL,
    PRIMARY KEY (tenant_id, channel_key, line_user_id)
)
"""

# 账号(tenant-first subject)→ 选定 OA;无行 = 旧默认 dms。
_ACCOUNT_CHANNELS = """
CREATE TABLE IF NOT EXISTS dms_account_line_channels (
    subject_id text PRIMARY KEY,
    channel_key text NOT NULL,
    updated_at timestamptz DEFAULT now(),
    updated_by uuid
)
"""

_TABLES = (
    "line_dms_bindings",
    "line_dms_binding_codes",
    "dms_line_sessions",
    "dms_account_line_channels",
)

# 多 OA 迁移(幂等):channel_key 列 + 复合唯一。绑定/会话的键从「全局 LINE id」改成
# 「(channel_key, LINE id)」—— 同一个人在不同 OA 下可能是同一个 userId,任何阶段都不许串 OA。
_MIGRATIONS = (
    "ALTER TABLE line_dms_bindings ADD COLUMN IF NOT EXISTS channel_key text NOT NULL DEFAULT 'dms'",
    "ALTER TABLE line_dms_binding_codes ADD COLUMN IF NOT EXISTS "
    "channel_key text NOT NULL DEFAULT 'dms'",
    "ALTER TABLE dms_line_sessions ADD COLUMN IF NOT EXISTS "
    "channel_key text NOT NULL DEFAULT 'dms'",
    "ALTER TABLE line_dms_bindings DROP CONSTRAINT IF EXISTS line_dms_bindings_line_user_id_key",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_line_dms_bindings_channel_line "
    "ON line_dms_bindings (channel_key, line_user_id)",
    "CREATE INDEX IF NOT EXISTS ix_line_dms_bindings_user ON line_dms_bindings (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_line_dms_bindings_tenant ON line_dms_bindings (tenant_id)",
    "CREATE INDEX IF NOT EXISTS ix_line_dms_binding_codes_user "
    "ON line_dms_binding_codes (user_id)",
)

# 旧会话表 PK=(tenant_id, line_user_id) 容不下「同租户同人在两个 OA」→ 换成含 channel 的 PK。
_SESSIONS_PK = """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'dms_line_sessions'::regclass
          AND contype = 'p'
          AND pg_get_constraintdef(oid) NOT LIKE '%channel_key%'
    ) THEN
        ALTER TABLE dms_line_sessions DROP CONSTRAINT dms_line_sessions_pkey;
        ALTER TABLE dms_line_sessions ADD PRIMARY KEY (tenant_id, channel_key, line_user_id);
    END IF;
END $$;
"""


def ensure_tables() -> None:
    """幂等建三表 + 多 OA 迁移 + apply_tenant_rls(首用自愈调)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended('line_dms_schema_v2', 0))")
        cur.execute(_BINDINGS)
        cur.execute(_BINDING_CODES)
        cur.execute(_SESSIONS)
        cur.execute(_ACCOUNT_CHANNELS)
        for statement in _MIGRATIONS:
            cur.execute(statement)
        cur.execute(_SESSIONS_PK)
        apply_tenant_rls(cur, "line_dms_bindings", "line_dms_binding_codes", "dms_line_sessions")


def _with_heal(fn):
    """表不存在(新库/回滚后)→ 建表重试一次;其余异常向上抛由调用方兜底。"""
    try:
        return fn()
    except Exception as e:
        if not any(t in str(e) for t in _TABLES):
            raise
        ensure_tables()
        return fn()
