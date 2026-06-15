"""LINE 卡片动作一次性令牌 line_action_nonces(防重放 · PO-12)。

Revision ID: 0037_line_action_nonces
Revises: 0036_purchase_auto_book
Create Date: 2026-06-16

数据卡 postback 动作(确认入账/撤销/丢弃)带一次性 token:发卡 mint 入库,点击 consume
原子消费,重复点击只第一次生效。token 即能力凭证 → 服务端据它反查目标记录。TTL 72h。
隔离=应用层 WHERE tenant_id;ENABLE RLS 兜底。
Dual-run:services/line_binding/line_action_nonce.ensure_table()(prod 无 alembic 钩子,走 ensure;本文件留档)。
"""

from alembic import op

revision = "0037_line_action_nonces"
down_revision = "0036_purchase_auto_book"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE line_action_nonces ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON line_action_nonces;
    CREATE POLICY tenant_isolation ON line_action_nonces
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
        CREATE TABLE IF NOT EXISTS line_action_nonces (
            token text PRIMARY KEY,
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            user_id text NOT NULL DEFAULT '',
            action_ref text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            expires_at timestamptz NOT NULL,
            consumed_at timestamptz
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_line_action_nonces_expires "
        "ON line_action_nonces (expires_at)"
    )
    op.execute(_RLS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS line_action_nonces")
