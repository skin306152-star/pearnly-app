"""POS 收银员按人权限(caps):pos_cashiers 加 caps jsonb(PC-1a · docs/pos/05)。

Revision ID: 0068_pos_cashier_caps
Revises: 0067_workorder_freeze_evidence
Create Date: 2026-07-11

纯收银员(未绑主账号)的折扣上限/可退可作废/改价/成本可见开关落在本列;绑主账号的
收银员权限仍由其 RBAC 生效码集换算(单一事实源,不读本列)。默认 '{}' = 全按最严默认
(见 services/pos/caps.CAP_DEFAULTS),存量行经 DEFAULT 天然补齐。
Dual-run:services/pos/cashier.ensure_core_schema() 跑同一幂等 ADD COLUMN IF NOT EXISTS。
"""

from alembic import op

revision = "0068_pos_cashier_caps"
down_revision = "0067_workorder_freeze_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE pos_cashiers "
        "ADD COLUMN IF NOT EXISTS caps jsonb NOT NULL DEFAULT '{}'::jsonb"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE pos_cashiers DROP COLUMN IF EXISTS caps")
