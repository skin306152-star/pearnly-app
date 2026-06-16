"""下线待归类:DROP intake_items。

Revision ID: 0040_drop_intake_items
Revises: 0039_auto_book_default_on
Create Date: 2026-06-16

待归类(intake_items)模块下线:LINE/拍照识别完的票一律建成采购草稿落列表,用户在列表里
改方向/补金额/删,系统不再单独兜一个待归类桶。存量 pending 项由 scripts/
migrate_intake_inbox_to_drafts.py 先转成草稿,再 DROP 表。downgrade 复原 0033 的表结构。
"""

from alembic import op

revision = "0040_drop_intake_items"
down_revision = "0039_auto_book_default_on"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE intake_items ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON intake_items;
    CREATE POLICY tenant_isolation ON intake_items
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
    op.execute("DROP TABLE IF EXISTS intake_items")


def downgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS intake_items (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            source text,
            raw jsonb,
            image_url text,
            ai_guess jsonb,
            status text NOT NULL DEFAULT 'pending',
            resolved_doc_id uuid,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_intake_items_ws "
        "ON intake_items (tenant_id, workspace_client_id, status)"
    )
    op.execute(_RLS)
