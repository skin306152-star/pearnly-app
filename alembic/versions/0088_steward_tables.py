# -*- coding: utf-8 -*-
"""智能管家(B2-M1)三表:steward_sessions / steward_messages / steward_tasks。

Revision ID: 0088_steward_tables
Revises: 0087_erp_bridge_tables
Create Date: 2026-07-26

为什么不复用工单表装管家任务:工单是会计业务对象(五态机 / 租约 / reaper / SoD 签批 /
事件流唯一事实源),管家任务是一次对话的交互编排记录(哪几步、跑到哪、产出什么链接),
混用会污染工单语义——矩阵、看板、reaper 会把管家的查询任务当成一张真月度工单。两者并存
不矛盾:管家将来真派出去的业务动作(开单/推送)仍旧落工单表,steward_tasks 只留编排痕迹。

steward_messages / steward_tasks 都自带 tenant_id(不靠 JOIN 回 sessions 取):RLS 是行级的,
子表没有 tenant_id 就没法写 policy。tenant RLS 照 ai_goal_contracts 先例。

留档性质:prod 不跑 alembic upgrade,真正落表靠 services/steward/store.ensure_tables()
首次使用时幂等自愈(与本迁移逐字对齐)。
"""

from alembic import op

revision = "0088_steward_tables"
down_revision = "0087_erp_bridge_tables"
branch_labels = None
depends_on = None

_RLS_TEMPLATE = """
    ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON {table};
    CREATE POLICY tenant_isolation ON {table}
    FOR ALL
    USING (
        tenant_id::text = current_setting('app.current_tenant_id', true)
        OR current_setting('app.bypass_rls', true) = 'on'
    )
    WITH CHECK (
        tenant_id::text = current_setting('app.current_tenant_id', true)
        OR current_setting('app.bypass_rls', true) = 'on'
    );
"""


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS steward_sessions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            user_id text NOT NULL,
            title text,
            created_at timestamptz NOT NULL DEFAULT now(),
            last_active_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS steward_tasks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            session_id uuid REFERENCES steward_sessions (id) ON DELETE CASCADE,
            title text NOT NULL DEFAULT '',
            status text NOT NULL DEFAULT 'running',
            steps jsonb NOT NULL DEFAULT '[]'::jsonb,
            artifacts jsonb NOT NULL DEFAULT '[]'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            finished_at timestamptz
        )
        """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS steward_messages (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            session_id uuid NOT NULL REFERENCES steward_sessions (id) ON DELETE CASCADE,
            role text NOT NULL,
            text text NOT NULL DEFAULT '',
            tool_trace jsonb NOT NULL DEFAULT '[]'::jsonb,
            task_id uuid,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_steward_sessions_tenant "
        "ON steward_sessions (tenant_id, last_active_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_steward_messages_session "
        "ON steward_messages (tenant_id, session_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_steward_tasks_session "
        "ON steward_tasks (tenant_id, session_id, created_at DESC)"
    )
    op.execute(_RLS_TEMPLATE.format(table="steward_sessions"))
    op.execute(_RLS_TEMPLATE.format(table="steward_tasks"))
    op.execute(_RLS_TEMPLATE.format(table="steward_messages"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS steward_messages")
    op.execute("DROP TABLE IF EXISTS steward_tasks")
    op.execute("DROP TABLE IF EXISTS steward_sessions")
