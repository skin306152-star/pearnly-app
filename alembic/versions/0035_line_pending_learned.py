"""一句话记账 · 多轮澄清会话态 line_pending_entry + 可学习词典 expense_learned。

Revision ID: 0035_line_pending_learned
Revises: 0034_expense_draft
Create Date: 2026-06-15

line_pending_entry:缺金额时存半成品(短 TTL),用户补一句后合并出卡(每 LINE 用户一条)。
expense_learned:用户改过的 关键词→科目 记下,下次同词直接对(越用越省)。
隔离=应用层 WHERE tenant_id + workspace_client_id;ENABLE RLS 兜底。
Dual-run:services/expense/schema.ensure_expense_schema()(prod 无 alembic 钩子,走 ensure;本文件留档)。
"""

from alembic import op

revision = "0035_line_pending_learned"
down_revision = "0034_expense_draft"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON {t};
    CREATE POLICY tenant_isolation ON {t}
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
        CREATE TABLE IF NOT EXISTS line_pending_entry (
            line_user_id text PRIMARY KEY,
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            draft jsonb NOT NULL DEFAULT '{}'::jsonb,
            missing text NOT NULL DEFAULT '',
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(_RLS.format(t="line_pending_entry"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS expense_learned (
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            keyword text NOT NULL,
            category_id uuid,
            subcategory_id uuid,
            category_name text NOT NULL DEFAULT '',
            subcategory_name text NOT NULL DEFAULT '',
            updated_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, workspace_client_id, keyword)
        )
        """)
    op.execute(_RLS.format(t="expense_learned"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS expense_learned")
    op.execute("DROP TABLE IF EXISTS line_pending_entry")
