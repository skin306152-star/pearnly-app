"""LINE 消息 ↔ 业务对象映射 line_message_refs(引用底座 · Brain OS P1A)。

Revision ID: 0041_line_message_refs
Revises: 0040_drop_intake_items
Create Date: 2026-06-17

发回执卡时记 LINE 消息 id → 绑定 purchase_doc。用户长按某条 reply「删除/改成X」→ webhook 带
quotedMessageId → 反查那张确切的单(不再默认改最近一笔)。隔离=应用层 WHERE tenant_id;
ENABLE RLS 兜底。Dual-run:services/line_binding/line_message_refs.ensure_table()(prod 无
alembic 钩子,走 ensure;本文件留档)。
"""

from alembic import op

revision = "0041_line_message_refs"
down_revision = "0040_drop_intake_items"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE line_message_refs ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON line_message_refs;
    CREATE POLICY tenant_isolation ON line_message_refs
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
        CREATE TABLE IF NOT EXISTS line_message_refs (
            line_message_id text PRIMARY KEY,
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            line_user_id text NOT NULL DEFAULT '',
            ref_type text NOT NULL DEFAULT 'purchase_doc',
            ref_id text NOT NULL,
            state text NOT NULL DEFAULT '',
            summary text NOT NULL DEFAULT '',
            created_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_line_message_refs_expires "
        "ON line_message_refs (expires_at)"
    )
    op.execute(_RLS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_message_refs")
