"""Per-document paper_size + doc_language on sales_documents (§E1 纸张 / 文档语言 · per-invoice).

Revision ID: 0020_sales_doc_paper_lang
Revises: 0019_sales_doc_copies_layout
Create Date: 2026-06-07

The wizard step-5 lets the user pick paper (A4/A5/80mm thermal) and document language
(th / th_en / th_zh) per invoice, but those choices were never persisted — the PDF always
rendered A4 + Thai/English. Add paper_size (default 'A4') and doc_language (default 'th_en',
= current behavior) so every later download/print/send follows the issued choice.

All defaulted -> backward compatible. Isolation app-layer (get_cursor_rls + WHERE tenant_id).
"""

from alembic import op

revision = "0020_sales_doc_paper_lang"
down_revision = "0019_sales_doc_copies_layout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE sales_documents "
        "ADD COLUMN IF NOT EXISTS paper_size text NOT NULL DEFAULT 'A4'"
    )
    op.execute(
        "ALTER TABLE sales_documents "
        "ADD COLUMN IF NOT EXISTS doc_language text NOT NULL DEFAULT 'th_en'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE sales_documents DROP COLUMN IF EXISTS doc_language")
    op.execute("ALTER TABLE sales_documents DROP COLUMN IF EXISTS paper_size")
