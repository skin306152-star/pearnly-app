"""Scope POS idempotency keys to tenant and workspace.

Revision ID: 0071_pos_client_uuid_scope
Revises: 0070_line_client_batch_seq
Create Date: 2026-07-12
"""

from alembic import op

revision = "0071_pos_client_uuid_scope"
down_revision = "0070_line_client_batch_seq"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE pos_sales DROP CONSTRAINT IF EXISTS pos_sales_client_uuid_key")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_sales_client_uuid_scope "
        "ON pos_sales (tenant_id, workspace_client_id, client_uuid)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_pos_sales_client_uuid_scope")
    op.execute(
        "ALTER TABLE pos_sales ADD CONSTRAINT pos_sales_client_uuid_key UNIQUE (client_uuid)"
    )
