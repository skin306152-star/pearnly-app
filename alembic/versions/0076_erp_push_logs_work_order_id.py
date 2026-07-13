# -*- coding: utf-8 -*-
"""erp_push_logs 补 work_order_id 可空列(MC2-C · 契约捎带小单)。

Revision ID: 0076_erp_push_logs_work_order_id
Revises: 0075_workorder_reaper_scan_index
Create Date: 2026-07-14

现状(窗B 验证+窗A 亲核):erp_push_logs 22 列无 work_order_id,T4c 回执核对
(services/workorder/steps/reconcile.py _run_shadow_gl_recon)只能按 invoice_no 在租户范围
内匹配,跨工单同票号理论上会串。本列补上后,工单发起的推送(未来写入点)可带上精确归属,
读侧优先按列匹配、无列值回落票号(见 push_log_queries.list_push_logs_by_invoice_nos)。

无外键约束(erp_push_logs 是 legacy 集成表,推送多为主站直推的独立流,不必强绑工单存在性)。
老行 NULL 如实,不回填(勘察硬结论:回填=编造工单归属)。

留档性质:prod alembic 指针停 0020,真正落列靠 services/erp/push_schema.py 的
ensure_erp_push_logs_work_order_id_column() 启动期自愈(dual-run,与本迁移逐字对齐,
tests/unit/test_push_retry_schema_contract.py 静态守)。
"""

from alembic import op

revision = "0076_erp_push_logs_work_order_id"
down_revision = "0075_workorder_reaper_scan_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE erp_push_logs ADD COLUMN IF NOT EXISTS work_order_id UUID")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_erp_push_logs_tenant_wo "
        "ON erp_push_logs (tenant_id, work_order_id) "
        "WHERE work_order_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_erp_push_logs_tenant_wo")
    op.execute("ALTER TABLE erp_push_logs DROP COLUMN IF EXISTS work_order_id")
