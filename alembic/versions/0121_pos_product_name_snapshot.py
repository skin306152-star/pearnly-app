"""Freeze the displayed product name on POS sale lines."""

from alembic import op

revision = "0121_pos_product_name_snapshot"
down_revision = "0120_erp_target_refresh_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE pos_sale_lines ADD COLUMN IF NOT EXISTS product_name_snapshot text")


def downgrade() -> None:
    op.execute("ALTER TABLE pos_sale_lines DROP COLUMN IF EXISTS product_name_snapshot")
