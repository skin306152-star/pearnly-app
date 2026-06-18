"""purchase_docs 加 payment_method(LINE 改付款落库 · P1E-2 后续)。

Revision ID: 0042_purchase_payment_method
Revises: 0041_line_message_refs
Create Date: 2026-06-18

此前 purchase_docs 只有 payment_status(paid/unpaid),付款方式仅作 OCR 卡片展示值、不落库,
故 LINE 内「改付款方式」只能甩详情页。加 payment_method 列(规范码 cash|transfer|promptpay|card,
认不出留原文)→ 建单持久化 OCR 识别值、LINE 内可直接改。Dual-run:prod 无 alembic 钩子,
走 services/purchase/schema.ensure_purchase_schema() 的幂等 ALTER;本文件留档。
"""

from alembic import op

revision = "0042_purchase_payment_method"
down_revision = "0041_line_message_refs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE purchase_docs ADD COLUMN IF NOT EXISTS payment_method text")


def downgrade() -> None:
    op.execute("ALTER TABLE purchase_docs DROP COLUMN IF EXISTS payment_method")
