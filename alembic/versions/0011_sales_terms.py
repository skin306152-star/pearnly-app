"""Due date + payment terms for credit sales (docs/16 §G4).

Revision ID: 0011_sales_terms
Revises: 0010_sales_discount
Create Date: 2026-06-06

B2B credit sales (tax_invoice issued unpaid) carry a due date and a free-text terms
string (e.g. "net 30"). Both nullable -> backward compatible. Isolation stays
app-layer; names written literally (a migration is a fixed snapshot).
"""

from alembic import op

revision = "0011_sales_terms"
down_revision = "0010_sales_discount"
branch_labels = None
depends_on = None

_DOC_COLUMNS = ("payment_terms", "due_date")


def upgrade() -> None:
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS due_date date")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS payment_terms text")


def downgrade() -> None:
    for col in _DOC_COLUMNS:
        op.execute(f"ALTER TABLE sales_documents DROP COLUMN IF EXISTS {col}")
