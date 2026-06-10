# -*- coding: utf-8 -*-
"""自动报税 schema 双跑入口(启动调一次 · 幂等 DDL · docs/tax-filing/01)。

prod 无自动迁移钩子 → startup 经 ensure_tax_schema() 幂等建 3 表(同 accounting 先例,
ensure-only 无 alembic 档)。隔离真正生效靠应用层 WHERE tenant_id + workspace_client_id;
RLS policy 是兜底(prod 现 BYPASSRLS)。一期一种一行(UNIQUE period,kind),已报(filed)
行为只读由应用层状态机保证。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS tax_filings (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        period text NOT NULL,
        kind text NOT NULL,
        status text NOT NULL DEFAULT 'prepared',
        net_amount numeric(14,2) NOT NULL DEFAULT 0,
        breakdown jsonb NOT NULL DEFAULT '{}'::jsonb,
        anomalies jsonb NOT NULL DEFAULT '[]'::jsonb,
        due_date date,
        filed_method text,
        receipt_no text,
        filed_at timestamptz,
        filed_by uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS filing_lines (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        filing_id uuid NOT NULL
            REFERENCES tax_filings (id) ON DELETE CASCADE,
        payee_name text,
        payee_tax_id text,
        payee_type text NOT NULL DEFAULT 'juristic',
        income_type text NOT NULL DEFAULT 'service',
        base_amount numeric(14,2) NOT NULL DEFAULT 0,
        wht_rate numeric(5,2),
        wht_amount numeric(14,2) NOT NULL DEFAULT 0,
        source_purchase_id uuid,
        cert_url text,
        cert_status text NOT NULL DEFAULT 'generated',
        sort int NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tax_settings (
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        vat_registered boolean NOT NULL DEFAULT TRUE,
        branch_type text NOT NULL DEFAULT 'main',
        branch_no text,
        efiling_connected boolean NOT NULL DEFAULT FALSE,
        efiling_credential_ref text,
        remind_days_before int NOT NULL DEFAULT 3,
        file_zero boolean NOT NULL DEFAULT TRUE,
        updated_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, workspace_client_id)
    )
    """,
)

_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_tax_filings_period_kind "
    "ON tax_filings (tenant_id, workspace_client_id, period, kind)",
    "CREATE INDEX IF NOT EXISTS ix_filing_lines_filing " "ON filing_lines (tenant_id, filing_id)",
)

_RLS_TABLES = ("tax_filings", "filing_lines", "tax_settings")


def ensure_tax_schema() -> None:
    """幂等建报税 3 表 + 索引 + RLS(startup 调)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)
