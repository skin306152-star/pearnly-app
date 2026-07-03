"""跨轮对话锚点表 line_agent_anchors(「把刚才那张推进 ERP」的指代记忆)。

Revision ID: 0048_line_agent_anchors
Revises: 0047_agent_turn_logs
Create Date: 2026-07-03

每用户单行 upsert:最近一轮碰过的对象 id(anchors jsonb),TTL 45 分钟。
Dual-run:services/line_binding/line_anchor_store.ensure_table()
(prod 无 alembic 钩子,走首用 ensure 自愈;本文件留档)。
"""

from alembic import op

revision = "0048_line_agent_anchors"
down_revision = "0047_agent_turn_logs"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE line_agent_anchors ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON line_agent_anchors;
    CREATE POLICY tenant_isolation ON line_agent_anchors
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
        CREATE TABLE IF NOT EXISTS line_agent_anchors (
            tenant_id uuid NOT NULL,
            line_user_id text NOT NULL,
            anchors jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL,
            PRIMARY KEY (tenant_id, line_user_id)
        )
        """)
    op.execute(_RLS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_agent_anchors")
