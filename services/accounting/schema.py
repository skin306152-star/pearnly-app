# -*- coding: utf-8 -*-
"""自动做账 schema 双跑入口(启动调一次 · 幂等 DDL · docs/accounting/01)。

prod 无自动迁移钩子 → startup 经 ensure_accounting_schema() 幂等建 9 表(做账 6 + 银行对账 3)。
隔离真正生效
靠应用层 WHERE tenant_id + workspace_client_id;RLS policy 是兜底(prod 现 BYPASSRLS)。
防重复唯一索引为 partial(排除 void):撤销重做(unpost)后允许同 source 重新生成凭证。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

_TABLES = (
    """
    CREATE TABLE IF NOT EXISTS chart_of_accounts (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        code text NOT NULL,
        name_zh text NOT NULL,
        name_th text,
        acct_type text NOT NULL,
        parent_id uuid,
        is_preset boolean NOT NULL DEFAULT FALSE,
        is_active boolean NOT NULL DEFAULT TRUE,
        sort int NOT NULL DEFAULT 0,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS account_mappings (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        role text NOT NULL,
        account_id uuid NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS journal_vouchers (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        voucher_no text,
        voucher_date date NOT NULL,
        period text NOT NULL,
        source_type text NOT NULL,
        source_id uuid,
        source_ref text,
        description text,
        human_note text,
        rule_key text,
        confidence numeric(5,2) NOT NULL DEFAULT 0,
        source_tier text NOT NULL DEFAULT 'manual',
        method text NOT NULL DEFAULT 'suggested',
        status text NOT NULL DEFAULT 'pending_review',
        review_reason text,
        total_debit numeric(14,2) NOT NULL DEFAULT 0,
        total_credit numeric(14,2) NOT NULL DEFAULT 0,
        created_by text,
        reviewed_by uuid,
        reviewed_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS journal_lines (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        voucher_id uuid NOT NULL
            REFERENCES journal_vouchers (id) ON DELETE CASCADE,
        account_id uuid NOT NULL,
        dr_cr text NOT NULL,
        amount numeric(14,2) NOT NULL,
        memo text,
        sort int NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS accounting_settings (
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        auto_post boolean NOT NULL DEFAULT FALSE,
        auto_post_threshold numeric(5,2) NOT NULL DEFAULT 90,
        auto_post_rules jsonb NOT NULL DEFAULT '{}'::jsonb,
        accounting_standard text NOT NULL DEFAULT 'TFRS_NPAE',
        inventory_method text NOT NULL DEFAULT 'periodic',
        base_currency text NOT NULL DEFAULT 'THB',
        start_period text,
        closed_through text,
        updated_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, workspace_client_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS review_learned (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        scope_key text NOT NULL,
        decision jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    # 银行对账(docs/accounting/bank-recon-mj/04 §2):账户登记 + 持续流水池 + 凭证模板。
    # 解析复用 services/recon,存储独立新表(旧 bank_recon 三表零接触)。
    """
    CREATE TABLE IF NOT EXISTS acct_bank_accounts (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        bank_code text NOT NULL,
        account_label text,
        account_last4 text,
        coa_account_id uuid,
        last_closing_balance numeric(14,2),
        last_closing_date date,
        is_active boolean NOT NULL DEFAULT TRUE,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS acct_bank_lines (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        bank_account_id uuid NOT NULL
            REFERENCES acct_bank_accounts (id) ON DELETE CASCADE,
        line_date date NOT NULL,
        amount numeric(14,2) NOT NULL,
        direction text NOT NULL,
        description text,
        bank_ref text,
        import_batch_id uuid,
        source_file_sha256 text,
        status text NOT NULL DEFAULT 'unmatched',
        matched_voucher_id uuid,
        match_payload jsonb,
        matched_at timestamptz,
        matched_by uuid,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS acct_voucher_templates (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        name text NOT NULL,
        lines jsonb NOT NULL DEFAULT '[]'::jsonb,
        use_count int NOT NULL DEFAULT 0,
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS accounting_posting_failures (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        workspace_client_id bigint NOT NULL,
        operation text NOT NULL DEFAULT 'enqueue',
        source_type text NOT NULL,
        source_id text NOT NULL,
        status text NOT NULL DEFAULT 'pending',
        attempts int NOT NULL DEFAULT 0,
        last_error text,
        context jsonb NOT NULL DEFAULT '{}'::jsonb,
        created_by text,
        next_retry_at timestamptz,
        first_failed_at timestamptz NOT NULL DEFAULT now(),
        last_failed_at timestamptz NOT NULL DEFAULT now(),
        resolved_at timestamptz,
        updated_at timestamptz NOT NULL DEFAULT now()
    )
    """,
)

_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_coa_code "
    "ON chart_of_accounts (tenant_id, workspace_client_id, code)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_acct_mapping_role "
    "ON account_mappings (tenant_id, workspace_client_id, role)",
    # 防重复生成凭证;排除 void = unpost(撤销重做)后同 source 可重新生成(安全带②)
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_jv_source "
    "ON journal_vouchers (tenant_id, workspace_client_id, source_type, source_id) "
    "WHERE source_id IS NOT NULL AND status != 'void'",
    "CREATE INDEX IF NOT EXISTS ix_jv_ws_period "
    "ON journal_vouchers (tenant_id, workspace_client_id, period)",
    "CREATE INDEX IF NOT EXISTS ix_journal_lines_voucher "
    "ON journal_lines (tenant_id, voucher_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_review_learned_scope "
    "ON review_learned (tenant_id, workspace_client_id, scope_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_bank_account "
    "ON acct_bank_accounts (tenant_id, workspace_client_id, bank_code, "
    "COALESCE(account_last4, ''))",
    # 防同批重复行:NULL 描述/ref 在唯一索引里视为可区分 → COALESCE 兜底
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_bank_line_dedup "
    "ON acct_bank_lines (bank_account_id, line_date, amount, "
    "COALESCE(description, ''), COALESCE(bank_ref, ''))",
    "CREATE INDEX IF NOT EXISTS ix_bank_lines_status "
    "ON acct_bank_lines (tenant_id, workspace_client_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_bank_lines_date "
    "ON acct_bank_lines (tenant_id, workspace_client_id, line_date)",
    # 候选查询 NOT EXISTS(凭证是否已被流水关联)走此索引
    "CREATE INDEX IF NOT EXISTS ix_bank_lines_matched_voucher "
    "ON acct_bank_lines (tenant_id, workspace_client_id, matched_voucher_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_voucher_template_name "
    "ON acct_voucher_templates (tenant_id, workspace_client_id, name)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_acct_posting_failure_open "
    "ON accounting_posting_failures "
    "(tenant_id, workspace_client_id, operation, source_type, source_id) "
    "WHERE status IN ('pending', 'retrying')",
    "CREATE INDEX IF NOT EXISTS ix_acct_posting_failure_due "
    "ON accounting_posting_failures (tenant_id, next_retry_at, first_failed_at) "
    "WHERE status IN ('pending', 'retrying')",
)

_RLS_TABLES = (
    "chart_of_accounts",
    "account_mappings",
    "journal_vouchers",
    "journal_lines",
    "accounting_settings",
    "review_learned",
    "acct_bank_accounts",
    "acct_bank_lines",
    "acct_voucher_templates",
    "accounting_posting_failures",
)


def ensure_accounting_schema() -> None:
    """幂等建做账 9 表(做账 6 + 银行对账 3)+ 索引 + RLS(startup 调)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for idx in _INDEXES:
            cur.execute(idx)
        apply_tenant_rls(cur, *_RLS_TABLES)
