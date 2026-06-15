"""商户采购:purchase_settings 加 auto_book(自动入账开关 · 默认关)。

Revision ID: 0036_purchase_auto_book
Revises: 0035_line_pending_learned
Create Date: 2026-06-15

自动入账开关:开 → 拍照/上传/LINE 进来的高置信、字段齐、无重复的票直接建单并过账
(不用逐张复核);关(默认)→ 照常进复核屏/待归类。一套账一行(purchase_settings)。
Dual-run:services/purchase/schema._ALTERS 同源幂等 DDL(startup 调)。
"""

from alembic import op

revision = "0036_purchase_auto_book"
down_revision = "0035_line_pending_learned"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE purchase_settings "
        "ADD COLUMN IF NOT EXISTS auto_book boolean NOT NULL DEFAULT FALSE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE purchase_settings DROP COLUMN IF EXISTS auto_book")
