# -*- coding: utf-8 -*-
"""销项税对账三表 schema/DDL(REFACTOR-WA-B1 · 2026-05-29 从 vat_recon_store 抽出 · 纯搬家 0 逻辑改)

ensure_vat_recon_tables:启动期幂等建表(vat_report + reconciliation_task + reconciliation_row)。
vat_recon_store 顶部 re-import 回去当 facade · db.py / 调用点 / 契约测试零改。
"""

import logging

from core.rls import apply_tenant_or_user_rls, apply_tenant_via_parent_rls

logger = logging.getLogger(__name__)


def ensure_vat_recon_tables():
    """v118.32.0 · 销项税对账 3 张表 · 启动时幂等建"""
    try:
        with db.get_cursor(commit=True) as cur:

            # ── 1. vat_report(先建 · 被 reconciliation_task 外键引用)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vat_report (
                    id              BIGSERIAL PRIMARY KEY,
                    tenant_id       UUID,
                    user_id         UUID,
                    client_id       BIGINT REFERENCES clients(id) ON DELETE SET NULL,
                    period_year     INTEGER NOT NULL,
                    period_month    INTEGER NOT NULL CHECK (period_month BETWEEN 1 AND 12),
                    issuer_tax_id   TEXT,
                    issuer_name     TEXT,
                    issuer_branch   TEXT DEFAULT '00000',
                    source_file_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
                    parsed_rows     JSONB NOT NULL DEFAULT '[]'::jsonb,
                    total_amount_pre_vat NUMERIC(18, 2),
                    total_vat       NUMERIC(18, 2),
                    total_amount    NUMERIC(18, 2),
                    parser_version  TEXT,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_vat_report_tenant
                    ON vat_report(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_vat_report_client_period
                    ON vat_report(client_id, period_year, period_month);
                CREATE INDEX IF NOT EXISTS idx_vat_report_tax_id
                    ON vat_report(issuer_tax_id) WHERE issuer_tax_id IS NOT NULL;
            """)

            # ── 2. reconciliation_task
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reconciliation_task (
                    id                       BIGSERIAL PRIMARY KEY,
                    tenant_id                UUID,
                    user_id                  UUID NOT NULL,
                    client_id                BIGINT REFERENCES clients(id) ON DELETE SET NULL,
                    period_year              INTEGER NOT NULL,
                    period_month             INTEGER NOT NULL CHECK (period_month BETWEEN 1 AND 12),
                    vat_report_id            BIGINT REFERENCES vat_report(id) ON DELETE SET NULL,
                    invoice_count_archived   INTEGER NOT NULL DEFAULT 0,
                    invoice_count_supplement INTEGER NOT NULL DEFAULT 0,
                    report_row_count         INTEGER NOT NULL DEFAULT 0,
                    status                   TEXT NOT NULL DEFAULT 'created',
                    matched_count            INTEGER NOT NULL DEFAULT 0,
                    mismatched_count         INTEGER NOT NULL DEFAULT 0,
                    invoice_orphan_count     INTEGER NOT NULL DEFAULT 0,
                    report_orphan_count      INTEGER NOT NULL DEFAULT 0,
                    confidence_score         REAL,
                    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    completed_at             TIMESTAMPTZ
                );
                CREATE INDEX IF NOT EXISTS idx_recon_task_tenant
                    ON reconciliation_task(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_recon_task_user
                    ON reconciliation_task(user_id);
                CREATE INDEX IF NOT EXISTS idx_recon_task_client_period
                    ON reconciliation_task(client_id, period_year, period_month);
                CREATE INDEX IF NOT EXISTS idx_recon_task_status
                    ON reconciliation_task(status);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_recon_task_unique_period
                    ON reconciliation_task(client_id, period_year, period_month)
                    WHERE status <> 'failed';
            """)

            # ── 3. reconciliation_row
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reconciliation_row (
                    id                BIGSERIAL PRIMARY KEY,
                    task_id           BIGINT NOT NULL
                                        REFERENCES reconciliation_task(id) ON DELETE CASCADE,
                    invoice_id        UUID REFERENCES ocr_history(id) ON DELETE SET NULL,
                    report_row_no     INTEGER,
                    pair_confidence   REAL,
                    status            TEXT NOT NULL DEFAULT 'pending',
                    diff_fields       JSONB NOT NULL DEFAULT '{}'::jsonb,
                    diff_categories   TEXT,
                    ai_analysis       TEXT,
                    accountant_action TEXT NOT NULL DEFAULT 'pending',
                    notes             TEXT,
                    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_recon_row_task
                    ON reconciliation_row(task_id);
                CREATE INDEX IF NOT EXISTS idx_recon_row_task_status
                    ON reconciliation_row(task_id, status);
                CREATE INDEX IF NOT EXISTS idx_recon_row_invoice
                    ON reconciliation_row(invoice_id) WHERE invoice_id IS NOT NULL;
            """)

            # B8 RLS wave2:vat_report 旧库补 user_id 列(单用户账号 tenant 为空,靠 user 兜底可见),
            # 从已关联的 reconciliation_task 回填存量行(新行由 create_vat_report 直接写 user_id)。
            cur.execute("ALTER TABLE vat_report ADD COLUMN IF NOT EXISTS user_id UUID")
            cur.execute(
                "UPDATE vat_report v SET user_id = t.user_id "
                "FROM reconciliation_task t "
                "WHERE t.vat_report_id = v.id AND v.user_id IS NULL"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_vat_report_user "
                "ON vat_report(user_id) WHERE user_id IS NOT NULL"
            )

            # enroll:vat_report / reconciliation_task 含 tenant_id+user_id → tenant_or_user;
            # reconciliation_row 仅 task_id → 经 task 传递式隔离(hard point 1)。
            apply_tenant_or_user_rls(cur, "vat_report", "reconciliation_task")
            apply_tenant_via_parent_rls(
                cur, "reconciliation_row", parent="reconciliation_task", fk="task_id"
            )

            logger.info(
                "✅ vat_report + reconciliation_task + reconciliation_row 已就绪 (v118.32.0)"
            )
    except Exception as e:
        logger.error(f"ensure_vat_recon_tables failed: {e}")


from core import db  # noqa: E402 · 循环 import 解法(被 db 间接引)
