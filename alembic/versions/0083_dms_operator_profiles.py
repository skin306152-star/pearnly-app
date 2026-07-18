"""DMS 操作员花名册档案表 dms_operator_profiles(波3 · DL-8)。

Revision ID: 0083_dms_operator_profiles
Revises: 0082_dms_masters_cache
Create Date: 2026-07-19

老板租户下每个 DMS 操作员(销售/管理员)一行角色档案:user_id 复用 users 表主键(操作员
是租户下的 member 用户,不发明新实体),凭据落各自 erp_endpoints、LINE 绑定落 line_dms_bindings,
本表只存「显示名 + 角色 + 启停」这层老板可见的花名册元数据。tenant_id NOT NULL → apply_tenant_rls
隔离(ensure 侧同步施加)。

Dual-run:services/dms_roster/store.ensure_tables()(prod 无 alembic 钩子,走首用 ensure
自愈;本文件留档)。
"""

from alembic import op

revision = "0083_dms_operator_profiles"
down_revision = "0082_dms_masters_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS dms_operator_profiles (
            user_id uuid PRIMARY KEY,
            tenant_id uuid NOT NULL,
            display_name text NOT NULL,
            dms_role text NOT NULL CHECK (dms_role IN ('sales', 'admin')),
            status text NOT NULL DEFAULT 'active',
            created_at timestamptz DEFAULT now()
        )
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS dms_operator_profiles")
