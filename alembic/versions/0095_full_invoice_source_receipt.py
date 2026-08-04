# -*- coding: utf-8 -*-
"""全式税票记原 POS 小票号(SM 缺口批次 G2 · sales_documents 一列)。

Revision ID: 0095_full_invoice_source_receipt
Revises: 0094_pos_receipt_compliance
Create Date: 2026-08-05

- source_receipt_no:POS 简式小票升级全式税票时,票面法定引用「ออกแทนใบกำกับภาษี
  อย่างย่อเลขที่ …」(替代原简式票号)的数据源。现有 references_document_id 是
  sales_documents 自引用 UUID,装不下 pos_sales.receipt_no 字符串,故独立一列;
  开出时随单冻结,PDF 有值才印整行(同 Register No. 规则,不印空标签)。

留档性质:prod 不跑 alembic upgrade,真正生效靠 services/pos/upgrade.ensure_upgrade_schema()
启动期双跑(经 bootstrap_pos_schema)。SQL 逐字写死不 import(迁移是历史快照 · 同 0006 约定)。
"""

from alembic import op

revision = "0095_full_invoice_source_receipt"
down_revision = "0094_pos_receipt_compliance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS source_receipt_no text")


def downgrade() -> None:
    op.execute("ALTER TABLE sales_documents DROP COLUMN IF EXISTS source_receipt_no")
