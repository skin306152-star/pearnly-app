"""Agent 轮级审计表 agent_turn_logs(回放底座 · 摸排 P1)。

Revision ID: 0047_agent_turn_logs
Revises: 0046_line_webhook_events
Create Date: 2026-07-03

每轮对话落:结局 kind + 工具轨迹 + 耗时 + trace_id(与 ai_usage 网关日志同号)。
user_text 截断留存,90 天写时顺清。RLS 按 tenant。
Dual-run:services/agent/turn_log.ensure_table()(prod 无 alembic 钩子,走 ensure;本文件留档)。
"""

from alembic import op

revision = "0047_agent_turn_logs"
down_revision = "0046_line_webhook_events"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE agent_turn_logs ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON agent_turn_logs;
    CREATE POLICY tenant_isolation ON agent_turn_logs
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
        CREATE TABLE IF NOT EXISTS agent_turn_logs (
            id bigserial PRIMARY KEY,
            tenant_id uuid,
            user_id text,
            line_user_id text,
            trace_id text,
            lang text,
            user_text text NOT NULL DEFAULT '',
            result_kind text NOT NULL,
            tool_trace jsonb NOT NULL DEFAULT '[]'::jsonb,
            elapsed_ms integer,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_agent_turn_logs_tenant "
        "ON agent_turn_logs (tenant_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_agent_turn_logs_created ON agent_turn_logs (created_at)"
    )
    op.execute(_RLS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_turn_logs")
