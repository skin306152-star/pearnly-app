"""POS 售出留档到 Google Sheet:pos_sheets_settings(老板后台 · docs/pos UI 14-Google Sheet)。

Revision ID: 0058_pos_sheets_settings
Revises: 0057_export_oauth_return_to
Create Date: 2026-07-08

每个 (tenant, workspace) 一行:目标表 spreadsheet_id + tab_name + 开关。Google OAuth 凭据
复用 export_google_credentials(不重建一套)。Dual-run:services/pos/sheets_sync.ensure_schema()
跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0058_pos_sheets_settings"
down_revision = "0057_export_oauth_return_to"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_sheets_settings (
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            spreadsheet_id text,
            tab_name text NOT NULL DEFAULT 'POS',
            enabled boolean NOT NULL DEFAULT FALSE,
            updated_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, workspace_client_id)
        )
        """)
    op.execute("ALTER TABLE pos_sheets_settings ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON pos_sheets_settings")
    # 与 core.rls._POLICY 同源(迁移须 standalone 不 import 应用代码 · 故内联同样谓词)。
    op.execute("""
        CREATE POLICY tenant_isolation ON pos_sheets_settings
        FOR ALL
        USING (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
        WITH CHECK (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pos_sheets_settings")
