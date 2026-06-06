"""Percentage line discount + whole-document discount (docs/16 §D).

Revision ID: 0010_sales_discount
Revises: 0009_sales_buyer_and_payment
Create Date: 2026-06-06

The line already carries an absolute `discount`; this adds:
  - sales_document_lines.discount_pct: the percentage the operator typed, kept for
    display / audit. The computed absolute amount still lands in `discount` so the
    tax math and PDF stay driven by one value.
  - sales_documents.header_discount_amount / header_discount_pct: a whole-order
    discount applied on top of the line nets, prorated back across lines so the VAT
    base stays on the actually-charged amount (docs/16 §D2). The resolved absolute
    amount is stored; the percent is kept for reference.

All columns nullable or defaulted -> backward compatible. Isolation stays app-layer
(get_cursor_rls + DAL). Names are written literally (a migration is a fixed snapshot).
"""

from alembic import op

revision = "0010_sales_discount"
down_revision = "0009_sales_buyer_and_payment"
branch_labels = None
depends_on = None

_DOC_COLUMNS = ("header_discount_pct", "header_discount_amount")
_LINE_COLUMNS = ("discount_pct",)


def upgrade() -> None:
    op.execute(
        "ALTER TABLE sales_document_lines ADD COLUMN IF NOT EXISTS discount_pct numeric(5,2)"
    )
    op.execute(
        "ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS header_discount_amount "
        "numeric(14,2) NOT NULL DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS header_discount_pct numeric(5,2)"
    )


def downgrade() -> None:
    for col in _DOC_COLUMNS:
        op.execute(f"ALTER TABLE sales_documents DROP COLUMN IF EXISTS {col}")
    for col in _LINE_COLUMNS:
        op.execute(f"ALTER TABLE sales_document_lines DROP COLUMN IF EXISTS {col}")
