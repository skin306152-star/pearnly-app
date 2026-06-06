"""Seller (账套主体) invoicing fields + sales_documents seller link (PO-6).

Revision ID: 0008_sales_seller_fields
Revises: 0007_sales_doc_reference
Create Date: 2026-06-06

会计事务所代多家公司开票:卖方 = 账套主体(workspace_clients · 已有 name/tax_id)。
补齐合规税票要的卖方字段(地址/总分公司/电话/是否注册 VAT),并在 sales_documents
记录"以哪家账套(卖方)开"。全部可空/带默认,向后兼容;隔离仍走 app 层。
"""

from alembic import op

revision = "0008_sales_seller_fields"
down_revision = "0007_sales_doc_reference"
branch_labels = None
depends_on = None

_WS_COLUMNS = ("address", "branch", "phone", "vat_registered")


def upgrade() -> None:
    op.execute("ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS address text")
    # branch: สำนักงานใหญ่(总公司)/ สาขาที่ NN(分公司)· 默认总公司
    op.execute(
        "ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS branch text "
        "DEFAULT 'สำนักงานใหญ่'"
    )
    op.execute("ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS phone text")
    op.execute(
        "ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS vat_registered boolean "
        "NOT NULL DEFAULT true"
    )
    op.execute(
        "ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS seller_workspace_client_id bigint "
        "REFERENCES workspace_clients (id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_docs_seller "
        "ON sales_documents (tenant_id, seller_workspace_client_id) "
        "WHERE seller_workspace_client_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_sales_docs_seller")
    op.execute("ALTER TABLE sales_documents DROP COLUMN IF EXISTS seller_workspace_client_id")
    for col in _WS_COLUMNS:
        op.execute(f"ALTER TABLE workspace_clients DROP COLUMN IF EXISTS {col}")
