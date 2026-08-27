"""Add per-line goods/service classification to sales documents."""

from alembic import op

revision = "0107_sales_line_item_type"
down_revision = "0106_line_erp_channel"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE sales_document_lines ADD COLUMN IF NOT EXISTS "
        "item_type text NOT NULL DEFAULT 'goods'"
    )


def downgrade():
    op.execute("ALTER TABLE sales_document_lines DROP COLUMN IF EXISTS item_type")
