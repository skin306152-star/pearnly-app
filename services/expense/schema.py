# -*- coding: utf-8 -*-
"""一句话记账 schema 双跑入口(LINE 文本路 + 图片路共用的捕获草稿表 · docs/smart-intake/14)。

prod 无 alembic 钩子 → startup 经 ensure_expense_schema() 幂等建 expense_draft 表。
expense_draft = 录入捕获层(金额/分类/卖家),上游于 journal_vouchers(复式过账)——LINE 快记
先落这里成草稿,用户确认/网页复核后才下推。隔离靠应用层 WHERE tenant_id + workspace_client_id,
RLS 兜底(prod 现 BYPASSRLS)。字段对齐 services/ocr ThaiInvoice,图/文两路共用同一张草稿。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_TABLE = """
CREATE TABLE IF NOT EXISTS expense_draft (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    workspace_client_id bigint NOT NULL,
    source text NOT NULL DEFAULT 'line_text',
    status text NOT NULL DEFAULT 'draft',
    line_user_id text,
    raw_text text,
    document_type text NOT NULL DEFAULT '',
    amount numeric(14,2),
    qty numeric(14,3),
    unit_price numeric(14,2),
    currency text NOT NULL DEFAULT 'THB',
    expense_type text NOT NULL DEFAULT '',
    category text NOT NULL DEFAULT '',
    subcategory text NOT NULL DEFAULT '',
    category_id uuid,
    subcategory_id uuid,
    vendor_name text NOT NULL DEFAULT '',
    vendor_tax_id text NOT NULL DEFAULT '',
    invoice_number text NOT NULL DEFAULT '',
    doc_date date,
    vat_mode text NOT NULL DEFAULT 'included',
    vat_amount numeric(14,2),
    wht_amount numeric(14,2),
    note text NOT NULL DEFAULT '',
    confidence numeric(5,2) NOT NULL DEFAULT 0,
    created_by text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
)
"""

# 多轮澄清会话态(短 TTL):缺金额时存半成品,用户补一句后合并。每 LINE 用户至多一条(PK)。
_PENDING_TABLE = """
CREATE TABLE IF NOT EXISTS line_pending_entry (
    line_user_id text PRIMARY KEY,
    tenant_id uuid NOT NULL,
    workspace_client_id bigint NOT NULL,
    draft jsonb NOT NULL DEFAULT '{}'::jsonb,
    missing text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now()
)
"""

# 可学习归类词典:用户改过的 关键词→科目 记下,下次同词直接对(越用越省)。
_LEARNED_TABLE = """
CREATE TABLE IF NOT EXISTS expense_learned (
    tenant_id uuid NOT NULL,
    workspace_client_id bigint NOT NULL,
    keyword text NOT NULL,
    category_id uuid,
    subcategory_id uuid,
    category_name text NOT NULL DEFAULT '',
    subcategory_name text NOT NULL DEFAULT '',
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, workspace_client_id, keyword)
)
"""

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_expense_draft_ws_status "
    "ON expense_draft (tenant_id, workspace_client_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_expense_draft_invoice_no "
    "ON expense_draft (tenant_id, workspace_client_id, invoice_number)",
)

# 存量表补列(幂等):早于科目链接上线建的表无 category_id/subcategory_id。
_ALTERS = (
    "ALTER TABLE expense_draft ADD COLUMN IF NOT EXISTS category_id uuid",
    "ALTER TABLE expense_draft ADD COLUMN IF NOT EXISTS subcategory_id uuid",
)


def ensure_expense_schema() -> None:
    """幂等建 expense_draft / line_pending_entry / expense_learned + 补列 + 索引 + RLS(startup 调)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        cur.execute(_TABLE)
        cur.execute(_PENDING_TABLE)
        cur.execute(_LEARNED_TABLE)
        for alter in _ALTERS:
            cur.execute(alter)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, "expense_draft", "line_pending_entry", "expense_learned")
