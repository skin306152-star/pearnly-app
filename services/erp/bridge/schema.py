# -*- coding: utf-8 -*-
"""ERP 桥两张表的 schema:建表 DDL + 首用自愈。

prod 不跑 alembic upgrade(alembic/versions/0087 只留档)→ 表靠这里首次使用时幂等建出来,
照 services/line_dms 那套范式。DDL 与 0087 逐字对齐,改一处必同改另一处。
"""

from __future__ import annotations

BRIDGES = "erp_bridges"
JOBS = "bridge_jobs"

_DDL_BRIDGES = """
CREATE TABLE IF NOT EXISTS erp_bridges (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    name text NOT NULL,
    secret_hash text NOT NULL,
    role text NOT NULL DEFAULT 'read',
    effective_role text NOT NULL DEFAULT 'read',
    books jsonb NOT NULL DEFAULT '[]'::jsonb,
    bridge_version text,
    host text,
    last_seen_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
)
"""

_DDL_JOBS = """
CREATE TABLE IF NOT EXISTS bridge_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    bridge_id uuid NOT NULL,
    book_id text,
    kind text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'queued',
    result jsonb,
    error jsonb,
    lease_owner text,
    lease_expires_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz
)
"""


def ensure_tables() -> None:
    """幂等建表 + 索引 + tenant RLS(DDL 走 owner 连接;RLS 是应用层过滤之外的第二道防线)。"""
    from core import db
    from core.rls import apply_tenant_rls

    with db.get_cursor(commit=True) as cur:
        cur.execute(_DDL_BRIDGES)
        cur.execute(f"CREATE INDEX IF NOT EXISTS ix_erp_bridges_tenant ON {BRIDGES} (tenant_id)")
        cur.execute(_DDL_JOBS)
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS ix_bridge_jobs_bridge_status ON {JOBS} (bridge_id, status)"
        )
        apply_tenant_rls(cur, BRIDGES, JOBS)


def heal(fn):
    """表不存在(新库 / prod 未跑迁移)→ 建表重试一次;其余异常照抛。"""
    try:
        return fn()
    except Exception as e:
        if BRIDGES not in str(e) and JOBS not in str(e):
            raise
        ensure_tables()
        return fn()
