"""商户采购:suppliers(供应商主数据 · 套账隔离 · docs/purchasing/01)。

Revision ID: 0031_suppliers
Revises: 0030_product_units_workspace_client_id
Create Date: 2026-06-08

供应商归套账(workspace_client_id)不归租户:切公司只看本家。AI 拍票自动建为主,
手录兜底。tax_id 13 位可空(小供应商常无)。隔离=应用层 WHERE tenant_id;ENABLE RLS
+ policy 兜底。Dual-run:services/purchase/schema.ensure_purchase_schema() 跑同一幂等 DDL
(prod 无自动迁移)。
"""

from alembic import op

revision = "0031_suppliers"
down_revision = "0030_product_units_workspace_client_id"
branch_labels = None
depends_on = None

# 与 core.rls._POLICY 同源(迁移须 standalone 不 import 应用代码 · 故内联同样谓词)。
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
        CREATE TABLE IF NOT EXISTS suppliers (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            name text NOT NULL,
            tax_id text,
            branch_type text NOT NULL DEFAULT 'none',
            branch_no text,
            address text,
            phone text,
            note text,
            is_active boolean NOT NULL DEFAULT TRUE,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_suppliers_ws "
        "ON suppliers (tenant_id, workspace_client_id)"
    )
    # 防重:同一套账内同税号只一家(税号可空,空号不参与去重)。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_suppliers_taxid "
        "ON suppliers (tenant_id, workspace_client_id, tax_id) "
        "WHERE tax_id IS NOT NULL"
    )
    op.execute(_RLS.format(t="suppliers"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS suppliers")
