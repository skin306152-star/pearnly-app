"""F4(L2)供应商过账档案:按卖方税号记"这家通常现结还是赊账 / 货品还是费用"。

Revision ID: 0061_supplier_posting_profiles
Revises: 0060_ai_usage
Create Date: 2026-07-10

喂进 payment_verdict 六级漏斗的第四级判据(profile,见 services/erp/express_push/common.py)。
default_item_type 只存不自动消费:主站不拿它压过票面法定证据,留给工单线预填。

隔离=应用层 WHERE tenant_id;ENABLE RLS + policy 兜底(与 0031 suppliers 同款模板)。
Dual-run:services/purchase/schema.ensure_purchase_schema() 跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0061_supplier_posting_profiles"
down_revision = "0060_ai_usage"
branch_labels = None
depends_on = None

# 与 core.rls._TPL["tenant"] 同源(迁移须 standalone 不 import 应用代码 · 故内联同样谓词)。
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
        CREATE TABLE IF NOT EXISTS supplier_posting_profiles (
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            seller_tax_id text NOT NULL,
            default_payment text NOT NULL DEFAULT '',
            default_item_type text NOT NULL DEFAULT '',
            default_category_id uuid,
            default_erp_account text,
            source text NOT NULL DEFAULT '',
            updated_at timestamptz NOT NULL DEFAULT now(),
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, workspace_client_id, seller_tax_id)
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_supplier_posting_profiles_ws "
        "ON supplier_posting_profiles (tenant_id, workspace_client_id)"
    )
    op.execute(_RLS.format(t="supplier_posting_profiles"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS supplier_posting_profiles")
