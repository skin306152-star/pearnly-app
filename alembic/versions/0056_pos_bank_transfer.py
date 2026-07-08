"""POS 收款方式加银行转账:pos_payment_settings 加 4 列(老板后台 · docs/pos UI 13-收款设置)。

Revision ID: 0056_pos_bank_transfer
Revises: 0055_expense_learned_source
Create Date: 2026-07-08

新增 bank_transfer_enabled(默认关,不像 promptpay/card 默认开——银行信息要老板主动填了才
有意义开)+ bank_name/bank_account_no/bank_account_name(POS 专属,不复用 workspace_clients)。
Dual-run:services/pos/payment_settings.ensure_payment_schema() 跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0056_pos_bank_transfer"
down_revision = "0055_expense_learned_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE pos_payment_settings
        ADD COLUMN IF NOT EXISTS bank_transfer_enabled boolean NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS bank_name text,
        ADD COLUMN IF NOT EXISTS bank_account_no text,
        ADD COLUMN IF NOT EXISTS bank_account_name text
        """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE pos_payment_settings
        DROP COLUMN IF EXISTS bank_transfer_enabled,
        DROP COLUMN IF EXISTS bank_name,
        DROP COLUMN IF EXISTS bank_account_no,
        DROP COLUMN IF EXISTS bank_account_name
        """)
