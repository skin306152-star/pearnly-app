"""VAT-inclusive pricing toggle, document-level (docs/16 §C).

Revision ID: 0012_sales_price_includes_vat
Revises: 0011_sales_terms
Create Date: 2026-06-06

Thai B2B invoices are usually VAT-exclusive (the default, unchanged). Retail /
simplified receipts are often VAT-inclusive (the shelf price already carries 7%).
This adds a single document-level switch `price_includes_vat`; when true the VAT is
extracted from the entered amounts (vat = gross * rate/(100+rate)) instead of added on
top. The switch is per-document, not per-line (a mixed invoice would confuse buyers).

Defaulted (false) -> backward compatible. Isolation stays app-layer (get_cursor_rls +
DAL WHERE tenant_id); names written literally (a migration is a fixed snapshot).
"""

from alembic import op

revision = "0012_sales_price_includes_vat"
down_revision = "0011_sales_terms"
branch_labels = None
depends_on = None

_DOC_COLUMNS = ("price_includes_vat",)


def upgrade() -> None:
    op.execute(
        "ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS price_includes_vat "
        "boolean NOT NULL DEFAULT false"
    )


def downgrade() -> None:
    for col in _DOC_COLUMNS:
        op.execute(f"ALTER TABLE sales_documents DROP COLUMN IF EXISTS {col}")
