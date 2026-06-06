"""PromptPay proxy on seller + persisted WHT rate (docs/16 §L1/§L2).

Revision ID: 0015_sales_promptpay_wht
Revises: 0014_sales_pdf_archive
Create Date: 2026-06-06

L1 PromptPay: the seller (workspace_clients = the account whose books we keep) gets a
`promptpay_id` proxy (mobile / national-or-tax id / e-wallet) so an unpaid invoice can show a
scan-to-pay QR. L2 WHT: documents already store `wht_amount` but not the rate, so the invoice
could not print the bracket label (e.g. "WHT 3%"); persist `wht_rate` to render it.

All columns nullable -> backward compatible. Isolation stays app-layer (get_cursor_rls +
DAL WHERE tenant_id); names written literally (a migration is a fixed snapshot).
"""

from alembic import op

revision = "0015_sales_promptpay_wht"
down_revision = "0014_sales_pdf_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS promptpay_id text")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS wht_rate numeric(6,2)")


def downgrade() -> None:
    op.execute("ALTER TABLE workspace_clients DROP COLUMN IF EXISTS promptpay_id")
    op.execute("ALTER TABLE sales_documents DROP COLUMN IF EXISTS wht_rate")
