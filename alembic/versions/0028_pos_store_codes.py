"""收银台设备绑定店铺码:pos_store_codes(POS 项目 · docs/pos/04 §1b)。

Revision ID: 0028_pos_store_codes
Revises: 0027_restaurant_core
Create Date: 2026-06-07

每个 (tenant, workspace) 一个全局唯一店铺码(MTA-7K9Q)+ token_version。设备扫码/输码绑定 → 服务端
按码解析 (tenant, workspace) 签发长期店铺令牌;老板「重置」= 换码 + bump token_version 吊销旧设备。
隔离=应用层 WHERE tenant_id;ENABLE RLS + policy 兜底。Dual-run:
services/pos/store_binding.ensure_store_schema() 跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0028_pos_store_codes"
down_revision = "0027_restaurant_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_store_codes (
            id bigserial PRIMARY KEY,
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            code text NOT NULL,
            token_version integer NOT NULL DEFAULT 1,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, workspace_client_id)
        )
        """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_store_code ON pos_store_codes (code)")
    op.execute("ALTER TABLE pos_store_codes ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON pos_store_codes")
    op.execute("""
        CREATE POLICY tenant_isolation ON pos_store_codes
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
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON pos_store_codes")
    op.execute("DROP TABLE IF EXISTS pos_store_codes")
