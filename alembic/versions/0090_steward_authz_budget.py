# -*- coding: utf-8 -*-
"""管家授权卡 + 成本封顶(B3 第二段):steward_cost_entries 台账。

Revision ID: 0090_steward_authz_budget
Revises: 0089_steward_task_async
Create Date: 2026-07-27

成本封顶的判据台账(预留-结算两段式,见 services/steward/budget.py 顶注):ai_usage 是
fire-and-forget 允许丢行的观测台账,当封顶判据会漏计,故封顶自记一张小账。授权令牌复用
line_action_nonces(0037)、批文落 steward_tasks.payload(0089)—— 授权侧零新表。

留档性质:prod 不跑 alembic upgrade,真正建表靠 services/steward/budget.ensure_tables()
首用幂等自愈(与本迁移逐字对齐)。
"""

from alembic import op

revision = "0090_steward_authz_budget"
down_revision = "0089_steward_task_async"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS steward_cost_entries (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            session_id uuid NOT NULL,
            task_id uuid,
            cost_thb numeric(12, 6) NOT NULL DEFAULT 0,
            settled boolean NOT NULL DEFAULT false,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_steward_cost_entries_session "
        "ON steward_cost_entries (tenant_id, session_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS steward_cost_entries")
