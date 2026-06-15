"""LINE 短期对话记忆 line_chat_history(滚动窗口喂大脑上下文 · PO-15)。

Revision ID: 0038_line_chat_history
Revises: 0037_line_action_nonces
Create Date: 2026-06-16

存每个 LINE 用户最近若干条消息(user/bot),调大脑时取最近 N 条(24h 内)作上下文喂 Gemini。
写时顺手清 24h 前;读 LIMIT N。隔离=应用层 WHERE tenant_id;ENABLE RLS 兜底。
Dual-run:services/line_binding/line_chat_memory.ensure_table()(prod 无 alembic 钩子,走 ensure;本文件留档)。
"""

from alembic import op

revision = "0038_line_chat_history"
down_revision = "0037_line_action_nonces"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE line_chat_history ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON line_chat_history;
    CREATE POLICY tenant_isolation ON line_chat_history
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
        CREATE TABLE IF NOT EXISTS line_chat_history (
            id bigserial PRIMARY KEY,
            line_user_id text NOT NULL,
            tenant_id uuid NOT NULL,
            role text NOT NULL,
            content text NOT NULL DEFAULT '',
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_line_chat_history_user "
        "ON line_chat_history (line_user_id, created_at DESC)"
    )
    op.execute(_RLS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_chat_history")
