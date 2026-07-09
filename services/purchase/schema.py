# -*- coding: utf-8 -*-
"""商户采购 schema 双跑入口(启动调一次 · 与 alembic 0031-0033 同源幂等 DDL)。

prod 无自动迁移钩子 → startup 经 ensure_purchase_schema() 幂等建 7 表 + RLS policy(F4 起
含 supplier_posting_profiles · alembic/versions/0061_supplier_posting_profiles.py 留档)。
DDL 与迁移逐字对齐(改一处必同改两处)。失败仅告警不 raise(不挡主服务)。隔离真正生效
靠应用层 WHERE tenant_id;RLS policy 是最小权限角色的兜底(prod 现 BYPASSRLS)。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS suppliers (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        name text NOT NULL,
        tax_id text,
        branch_type text NOT NULL DEFAULT 'none',
        branch_no text,
        address text,
        phone text,
        note text,
        is_active boolean NOT NULL DEFAULT TRUE,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS purchase_docs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        doc_kind text NOT NULL,
        supplier_id uuid,
        doc_no text,
        doc_date date,
        has_vat boolean NOT NULL DEFAULT FALSE,
        currency text NOT NULL DEFAULT 'THB',
        fx_rate numeric(14,6) NOT NULL DEFAULT 1,
        subtotal numeric(14,2) NOT NULL DEFAULT 0,
        discount_total numeric(14,2) NOT NULL DEFAULT 0,
        vat_amount numeric(14,2) NOT NULL DEFAULT 0,
        wht_amount numeric(14,2) NOT NULL DEFAULT 0,
        rounding numeric(14,2) NOT NULL DEFAULT 0,
        grand_total numeric(14,2) NOT NULL DEFAULT 0,
        net_payable numeric(14,2) NOT NULL DEFAULT 0,
        category_id uuid,
        requester text,
        requester_user_id uuid,
        approval_status text NOT NULL DEFAULT 'none',
        payment_status text NOT NULL DEFAULT 'unpaid',
        payment_method text,
        paid_amount numeric(14,2) NOT NULL DEFAULT 0,
        due_date date,
        source text,
        ocr_raw jsonb,
        dedupe_key text,
        image_sha256 text,
        status text NOT NULL DEFAULT 'draft',
        amount_override boolean NOT NULL DEFAULT FALSE,
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS purchase_lines (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        purchase_doc_id uuid NOT NULL
            REFERENCES purchase_docs (id) ON DELETE CASCADE,
        line_no int NOT NULL DEFAULT 1,
        item_type text NOT NULL DEFAULT 'goods',
        product_id uuid,
        description text,
        qty numeric(14,3) NOT NULL DEFAULT 0,
        unit text,
        unit_price numeric(14,2) NOT NULL DEFAULT 0,
        discount numeric(14,2) NOT NULL DEFAULT 0,
        line_total numeric(14,2) NOT NULL DEFAULT 0,
        vat_rate numeric(5,2) NOT NULL DEFAULT 7,
        vat_applicable boolean NOT NULL DEFAULT TRUE,
        wht_rate numeric(5,2) NOT NULL DEFAULT 0,
        category_id uuid,
        subcategory_id uuid,
        batch_no text,
        expiry_date date
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS expense_categories (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        parent_id uuid REFERENCES expense_categories (id) ON DELETE CASCADE,
        name text NOT NULL,
        is_active boolean NOT NULL DEFAULT TRUE,
        sort int NOT NULL DEFAULT 0,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS purchase_settings (
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        default_vat_rate numeric(5,2) NOT NULL DEFAULT 7,
        auto_stock_in boolean NOT NULL DEFAULT FALSE,
        dedupe_block boolean NOT NULL DEFAULT TRUE,
        default_due_days int NOT NULL DEFAULT 0,
        pay_needs_approval boolean NOT NULL DEFAULT FALSE,
        default_wht_service_rate numeric(5,2) NOT NULL DEFAULT 3,
        base_currency text NOT NULL DEFAULT 'THB',
        auto_book boolean NOT NULL DEFAULT TRUE,
        updated_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, workspace_client_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS purchase_attachments (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        purchase_doc_id uuid NOT NULL
            REFERENCES purchase_docs (id) ON DELETE CASCADE,
        kind text NOT NULL,
        url text,
        generated boolean NOT NULL DEFAULT FALSE,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS supplier_posting_profiles (
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        seller_tax_id text NOT NULL,
        default_payment text NOT NULL DEFAULT '',
        default_item_type text NOT NULL DEFAULT '',
        default_category_id uuid,
        default_erp_account text,
        source text NOT NULL DEFAULT '',
        updated_at timestamptz NOT NULL DEFAULT now(),
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, workspace_client_id, seller_tax_id)
    )
    """,
)

_INDEXES = (
    "CREATE INDEX IF NOT EXISTS ix_suppliers_ws " "ON suppliers (tenant_id, workspace_client_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_suppliers_taxid "
    "ON suppliers (tenant_id, workspace_client_id, tax_id) WHERE tax_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_purchase_docs_ws "
    "ON purchase_docs (tenant_id, workspace_client_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_purchase_docs_dedupe "
    "ON purchase_docs (tenant_id, workspace_client_id, dedupe_key) "
    "WHERE dedupe_key IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_purchase_docs_image_sha "
    "ON purchase_docs (tenant_id, workspace_client_id, image_sha256) "
    "WHERE image_sha256 IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_purchase_lines_doc "
    "ON purchase_lines (tenant_id, purchase_doc_id)",
    "CREATE INDEX IF NOT EXISTS ix_expense_categories_ws "
    "ON expense_categories (tenant_id, workspace_client_id)",
    "CREATE INDEX IF NOT EXISTS ix_purchase_attachments_doc "
    "ON purchase_attachments (tenant_id, purchase_doc_id)",
    "CREATE INDEX IF NOT EXISTS ix_supplier_posting_profiles_ws "
    "ON supplier_posting_profiles (tenant_id, workspace_client_id)",
)

# 存量表补列(prod 已建表 → CREATE IF NOT EXISTS 不补列 · 须 ALTER 自愈幂等)。
_ALTERS = (
    "ALTER TABLE purchase_docs "
    "ADD COLUMN IF NOT EXISTS amount_override boolean NOT NULL DEFAULT FALSE",
    "ALTER TABLE purchase_settings "
    "ADD COLUMN IF NOT EXISTS auto_book boolean NOT NULL DEFAULT TRUE",
    "ALTER TABLE purchase_docs ADD COLUMN IF NOT EXISTS payment_method text",
    "ALTER TABLE purchase_docs ADD COLUMN IF NOT EXISTS image_sha256 text",
)

_RLS_TABLES = (
    "suppliers",
    "purchase_docs",
    "purchase_lines",
    "expense_categories",
    "purchase_settings",
    "purchase_attachments",
    "supplier_posting_profiles",
)


def ensure_purchase_schema() -> None:
    """幂等建采购 7 表 + 索引 + RLS(startup 调 · 与 alembic 0031-0033/0061 双跑)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for alt in _ALTERS:
            cur.execute(alt)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)
