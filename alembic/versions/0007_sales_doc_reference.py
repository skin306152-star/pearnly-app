"""Sales documents: reference columns for credit/debit notes (PO-5).

Revision ID: 0007_sales_doc_reference
Revises: 0006_sales_core
Create Date: 2026-06-06

红冲(ใบลดหนี้)/ 补开(ใบเพิ่มหนี้)复用 sales_documents(doc_type=credit_note/
debit_note),引用被冲的原始已开出发票。这里加两列:references_document_id(指原单)
+ reference_reason(冲销原因)。两列可空——普通发票不引用任何单。

幂等:ADD COLUMN IF NOT EXISTS。隔离仍走 app 层(tenant_id + get_cursor_rls),不在
迁移建 RLS policy。
"""

from alembic import op

revision = "0007_sales_doc_reference"
down_revision = "0006_sales_core"
branch_labels = None
depends_on = None

_COLUMNS = ("references_document_id", "reference_reason")


def upgrade() -> None:
    op.execute(
        "ALTER TABLE sales_documents "
        "ADD COLUMN IF NOT EXISTS references_document_id uuid "
        "REFERENCES sales_documents (id)"
    )
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS reference_reason text")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_docs_references "
        "ON sales_documents (tenant_id, references_document_id) "
        "WHERE references_document_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_sales_docs_references")
    for col in _COLUMNS:
        op.execute(f"ALTER TABLE sales_documents DROP COLUMN IF EXISTS {col}")
