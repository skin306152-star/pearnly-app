"""Issued-document PDF retention hash (docs/16 §E3).

Revision ID: 0014_sales_pdf_archive
Revises: 0013_sales_approval
Create Date: 2026-06-06

Thai law requires a tax invoice and its copy be reproducible and unaltered for >=5 years.
The frozen data (parties_snapshot + frozen lines/totals) already makes a document byte-for-byte
reproducible. This adds the audit hash: at issue time we deterministically render the canonical
archival PDF (A4 / original) and store its sha256, so a re-render can be verified against the
original. `pdf_url` is reserved for an object-storage copy (not populated yet -> nullable).

All columns nullable -> backward compatible. Isolation stays app-layer (get_cursor_rls +
DAL WHERE tenant_id); names written literally (a migration is a fixed snapshot).
"""

from alembic import op

revision = "0014_sales_pdf_archive"
down_revision = "0013_sales_approval"
branch_labels = None
depends_on = None

_DOC_COLUMNS = ("pdf_url", "pdf_sha256")


def upgrade() -> None:
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS pdf_sha256 text")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS pdf_url text")


def downgrade() -> None:
    for col in _DOC_COLUMNS:
        op.execute(f"ALTER TABLE sales_documents DROP COLUMN IF EXISTS {col}")
