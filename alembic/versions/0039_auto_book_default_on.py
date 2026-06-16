"""auto_book 默认翻为开(高置信直接入账为默认 · 决策1/PO-11)+ 回填存量行。

Revision ID: 0039_auto_book_default_on
Revises: 0038_line_chat_history
Create Date: 2026-06-16

统一文/图入账编排后,高置信默认直接入正式账(可撤销),auto_book=关 时才确认优先。
把列默认 FALSE→TRUE,并一次性回填存量 FALSE 行 → 现有租户也享默认直接入账。
Dual-run:services/purchase/schema._flip_auto_book_default_on()(prod 无 alembic 钩子,
走 ensure 一次性翻转;本文件留档)。
"""

from alembic import op

revision = "0039_auto_book_default_on"
down_revision = "0038_line_chat_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE purchase_settings SET auto_book = TRUE WHERE auto_book = FALSE")
    op.execute("ALTER TABLE purchase_settings ALTER COLUMN auto_book SET DEFAULT TRUE")


def downgrade() -> None:
    op.execute("ALTER TABLE purchase_settings ALTER COLUMN auto_book SET DEFAULT FALSE")
