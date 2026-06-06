"""Issue approval workflow audit columns (docs/16 §F).

Revision ID: 0013_sales_approval
Revises: 0012_sales_price_includes_vat
Create Date: 2026-06-06

Some firms want an owner to approve before a draft is issued (takes a number); others
issue directly. The policy (`approval_mode` = none|single) lives in tenant settings
(sales_settings, a later migration), not on the document. The document only records the
workflow audit: who approved and when, and the reason if rejected. The extra workflow
states (`pending_approval`, `rejected`) reuse the existing free-text `status` column, so
no enum change is needed here.

All columns nullable -> backward compatible. Isolation stays app-layer (get_cursor_rls +
DAL WHERE tenant_id); names written literally (a migration is a fixed snapshot).
"""

from alembic import op

revision = "0013_sales_approval"
down_revision = "0012_sales_price_includes_vat"
branch_labels = None
depends_on = None

_DOC_COLUMNS = ("rejected_reason", "approved_at", "approved_by")


def upgrade() -> None:
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS approved_by text")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS approved_at timestamptz")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS rejected_reason text")


def downgrade() -> None:
    for col in _DOC_COLUMNS:
        op.execute(f"ALTER TABLE sales_documents DROP COLUMN IF EXISTS {col}")
