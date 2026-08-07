# -*- coding: utf-8 -*-
"""OCR 确认→正式单据转换桥:purchase_docs/sales_documents 挂 ocr_history_id(溯源+防重)。

Revision ID: 0098_docs_ocr_history_link
Revises: 0097_stock_card_openings
Create Date: 2026-08-07

背景:录入工作台「确认」此前只翻 ocr_history.staged(services/ocr_history/mutations.
commit_staged_ocr_history),不落 purchase_docs/sales_documents —— 收发存报表读的正是
这两张表(status='posted'/'issued'),于是"确认完≠过账完",报表恒空。services/intake_bridge
把确认接上真实建账,一张 history 只转一次全靠这列(tenant_id, ocr_history_id) 部分唯一索引
挡重复转换(仿 work_order_items.ocr_history_id 溯源惯例,docs/db/prod-schema.sql:3137)。

两列都可空(NULL=非本桥落的单据,含存量数据与手工录入),故索引带 WHERE 谓词只管非空值,
不挡历史空值互相"重复"。Dual-run:services/intake_bridge/schema.ensure_intake_bridge_schema()
跑同一 DDL(prod 无自动迁移钩子,真正建列靠 startup 幂等自愈)。
"""

from alembic import op

revision = "0098_docs_ocr_history_link"
down_revision = "0097_stock_card_openings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE purchase_docs ADD COLUMN IF NOT EXISTS ocr_history_id uuid")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS ocr_history_id uuid")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_purchase_docs_ocr_history "
        "ON purchase_docs (tenant_id, ocr_history_id) WHERE ocr_history_id IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_documents_ocr_history "
        "ON sales_documents (tenant_id, ocr_history_id) WHERE ocr_history_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_purchase_docs_ocr_history")
    op.execute("DROP INDEX IF EXISTS uq_sales_documents_ocr_history")
    op.execute("ALTER TABLE purchase_docs DROP COLUMN IF EXISTS ocr_history_id")
    op.execute("ALTER TABLE sales_documents DROP COLUMN IF EXISTS ocr_history_id")
