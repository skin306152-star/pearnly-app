"""Google OAuth state 加 return_to:一份凭据服务多个集成入口(采购导出/POS)。

Revision ID: 0057_export_oauth_return_to
Revises: 0056_pos_bank_transfer
Create Date: 2026-07-08

回调最终跳转目标随发起连接的页面而定(见 routes/google_oauth_routes.py _RETURN_TARGETS)。
默认值保原有行为(旧 state 行/没传参数一律回采购导出页)。Dual-run:
services/export/schema.ensure_export_schema() 跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0057_export_oauth_return_to"
down_revision = "0056_pos_bank_transfer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE export_oauth_states "
        "ADD COLUMN IF NOT EXISTS return_to text NOT NULL DEFAULT 'purchase-export'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE export_oauth_states DROP COLUMN IF EXISTS return_to")
