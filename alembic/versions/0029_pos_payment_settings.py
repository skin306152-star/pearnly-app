"""POS 收款设置:pos_payment_settings(老板后台 · docs/pos UI 13-收款设置)。

Revision ID: 0029_pos_payment_settings
Revises: 0028_pos_store_codes
Create Date: 2026-06-08

每个 (tenant, workspace) 一行收款设置:支付方式开关(现金恒开 · PromptPay/刷卡可关)+ 服务费率
+ 价格含 VAT。PromptPay 收款 ID 复用 workspace_clients.promptpay_id(不重复存)。隔离=应用层
WHERE tenant_id;ENABLE RLS + policy 兜底。Dual-run:services/pos/payment_settings.ensure_payment_schema()
跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0029_pos_payment_settings"
down_revision = "0028_pos_store_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_payment_settings (
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            promptpay_enabled boolean NOT NULL DEFAULT TRUE,
            card_enabled boolean NOT NULL DEFAULT TRUE,
            service_charge_rate numeric(6,2) NOT NULL DEFAULT 0,
            price_includes_vat boolean NOT NULL DEFAULT TRUE,
            updated_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, workspace_client_id)
        )
        """)
    op.execute("ALTER TABLE pos_payment_settings ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON pos_payment_settings")
    # 与 core.rls._POLICY 同源(迁移须 standalone 不 import 应用代码 · 故内联同样谓词)。
    op.execute("""
        CREATE POLICY tenant_isolation ON pos_payment_settings
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
    op.execute("DROP TABLE IF EXISTS pos_payment_settings")
