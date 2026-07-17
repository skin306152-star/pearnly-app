"""DMS 独立 LINE 通道三表 line_dms_bindings / line_dms_binding_codes / dms_line_sessions(DL-1)。

Revision ID: 0081_line_dms_channel
Revises: 0080_tenant_entrances_dms
Create Date: 2026-07-17

独立产品 Pearnly DMS 的 LINE 绑定/绑定码/会话态,与老会计站 line_bindings 完全隔离。
三表均含 tenant_id → apply_tenant_rls 隔离(ensure 侧同步施加)。
Dual-run:services/line_dms/store.ensure_tables()(prod 无 alembic 钩子,走首用 ensure
自愈;本文件留档)。
"""

from alembic import op

revision = "0081_line_dms_channel"
down_revision = "0080_tenant_entrances_dms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS line_dms_bindings (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            line_user_id text UNIQUE,
            tenant_id uuid NOT NULL,
            user_id uuid NOT NULL,
            display_name text,
            bound_at timestamptz DEFAULT now(),
            last_active_at timestamptz
        )
        """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS line_dms_binding_codes (
            code text PRIMARY KEY,
            tenant_id uuid,
            user_id uuid,
            expires_at timestamptz,
            used_at timestamptz
        )
        """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS dms_line_sessions (
            tenant_id uuid NOT NULL,
            line_user_id text NOT NULL,
            state text,
            payload jsonb DEFAULT '{}',
            expires_at timestamptz NOT NULL,
            PRIMARY KEY (tenant_id, line_user_id)
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dms_line_sessions")
    op.execute("DROP TABLE IF EXISTS line_dms_binding_codes")
    op.execute("DROP TABLE IF EXISTS line_dms_bindings")
