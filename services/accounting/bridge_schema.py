# -*- coding: utf-8 -*-
"""科目桥 schema 双跑入口(启动调一次 · 与 alembic 0073 同源幂等 DDL · T4a)。

prod 无自动迁移钩子 → startup 经 ensure_coa_erp_bridge_schema() 幂等建表 + RLS policy。
DDL 与迁移逐字对齐(改一处必同改两处 · tests/unit/test_coa_erp_bridge_schema.py 静态守)。
纯 tenant 隔离(Supabase 自动给 public 新表开 RLS,照 0072 先例补 policy,免零-policy
deny-all 孤儿)。PK = (tenant, 账套, erp_type, coa_code) 天然承载 UNIQUE + 查询索引。
"""

from __future__ import annotations

from core.rls import apply_tenant_rls

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS coa_erp_bridge (
        tenant_id           uuid    NOT NULL,
        workspace_client_id bigint  NOT NULL,
        erp_type            text    NOT NULL,
        coa_code            text    NOT NULL,
        erp_code            text    NOT NULL,
        erp_name            text    NOT NULL DEFAULT '',
        match_source        text    NOT NULL DEFAULT 'manual',
        created_at          timestamptz NOT NULL DEFAULT now(),
        updated_at          timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, workspace_client_id, erp_type, coa_code)
    )
    """,
)

_RLS_TABLES = ("coa_erp_bridge",)


def ensure_coa_erp_bridge_schema() -> None:
    """幂等建科目桥表 + RLS(startup 调 · 与 alembic 0073 双跑)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        apply_tenant_rls(cur, *_RLS_TABLES)
