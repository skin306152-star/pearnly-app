"""Per-document copies_layout on sales_documents (§E2 正本+副本同页 · per-invoice).

Revision ID: 0019_sales_doc_copies_layout
Revises: 0018_sales_send
Create Date: 2026-06-07

The wizard step-5 lets the user pick single vs 正本+副本同页 (two_up) per invoice, but there was
no column to persist that choice — it was dropped and the PDF always rendered separate. Add
copies_layout on sales_documents (default 'separate', backward compatible); the /pdf endpoint reads
it when the request doesn't override, so any later download/print follows the issued layout.

All defaulted -> backward compatible. Isolation app-layer (get_cursor_rls + WHERE tenant_id).
"""

from alembic import op

revision = "0019_sales_doc_copies_layout"
down_revision = "0018_sales_send"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE sales_documents "
        "ADD COLUMN IF NOT EXISTS copies_layout text NOT NULL DEFAULT 'separate'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE sales_documents DROP COLUMN IF EXISTS copies_layout")
