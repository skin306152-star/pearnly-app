# -*- coding: utf-8 -*-
"""工资进料 schema 双跑入口(启动调一次 · 与 alembic 0072 同源幂等 DDL · 方案 §2.3/P4)。

prod 无自动迁移钩子 → startup 经 ensure_payroll_schema() 幂等建 2 表 + RLS policy。DDL 与
迁移逐字对齐(改一处必同改两处 · tests/unit/test_payroll_schema.py 静态守)。纯 tenant 隔离
(Supabase 自动给 public 新表开 RLS,照 0059/0064 先例补 policy,免零-policy deny-all 孤儿)。

  client_payroll_templates:每客户列映射模板(下月自动套 · PK 天然幂等 upsert)
  client_payroll_rows:月度进料行(供 ภ.ง.ด.1ก 年度聚合 + 义务追溯)
"""

from __future__ import annotations

from core.rls import apply_tenant_rls

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS client_payroll_templates (
        tenant_id           uuid    NOT NULL,
        workspace_client_id bigint  NOT NULL,
        column_map          jsonb   NOT NULL DEFAULT '{}'::jsonb,
        income_code         text    NOT NULL DEFAULT '40(1)',
        fixed_values        jsonb   NOT NULL DEFAULT '{}'::jsonb,
        header_hash         text    NOT NULL DEFAULT '',
        updated_at          timestamptz NOT NULL DEFAULT now(),
        created_at          timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, workspace_client_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS client_payroll_rows (
        id                  bigserial PRIMARY KEY,
        tenant_id           uuid    NOT NULL,
        workspace_client_id bigint  NOT NULL,
        period              text    NOT NULL,
        seq                 integer NOT NULL,
        employee_id         text    NOT NULL,
        title               text    NOT NULL DEFAULT '',
        first_name          text    NOT NULL DEFAULT '',
        last_name           text    NOT NULL DEFAULT '',
        income_code         text    NOT NULL DEFAULT '40(1)',
        paid_date           date,
        paid_amount         numeric(15,2) NOT NULL DEFAULT 0,
        wht_amount          numeric(15,2) NOT NULL DEFAULT 0,
        condition           text    NOT NULL DEFAULT '1',
        created_at          timestamptz NOT NULL DEFAULT now()
    )
    """,
)

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_payroll_rows_period "
    "ON client_payroll_rows (tenant_id, workspace_client_id, period)",
)

_RLS_TABLES = ("client_payroll_templates", "client_payroll_rows")


def ensure_payroll_schema() -> None:
    """幂等建工资进料 2 表 + 索引 + RLS(startup 调 · 与 alembic 0072 双跑)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)
