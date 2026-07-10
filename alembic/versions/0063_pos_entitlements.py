"""POS 买断授权(开通费 ค่าติดตั้งและเปิดใช้งาน)· PS-3 S 档一次性开通授权表。

Revision ID: 0063_pos_entitlements
Revises: 0062_pos_sale_line_cost
Create Date: 2026-07-10

一租户一行(UNIQUE tenant_id):付没付「开通费」+ 一套额度上限(店/收银员)。与 OCR 订阅解耦——
不进 tenant_subscriptions、不动 tenant_credits.balance;那笔钱只在 credit_transactions 记一行
type='pos_buyout' 作审计(见 services/pos/entitlements.grant)。开通即联动 apply_preset('pos_only')。

隔离=应用层 WHERE tenant_id;ENABLE RLS + policy 兜底(与 0028 pos_store_codes 同款模板)。
Dual-run:services/pos/entitlements.ensure_pos_entitlement_schema() 跑同一幂等 DDL(prod 无自动迁移)。

顺带把 credit_transactions.type CHECK 放宽收下 'pos_buyout'(审计行的类型 · 与
services/billing/credits_schema.ensure_credits_tables 的权威约束同源;两处不一致会在启动被对方 DROP+ADD 覆盖)。
"""

from alembic import op

revision = "0063_pos_entitlements"
down_revision = "0062_pos_sale_line_cost"
branch_labels = None
depends_on = None

# credit_transactions.type 放宽后的全集(权威定义在 credits_schema.py · 此处内联同款,升级路径也放开)。
_CT_TYPES = "'topup','usage','adjustment','subscription','pos_buyout'"
_CT_TYPES_PRE = "'topup','usage','adjustment','subscription'"

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


def _widen_ct_check(types: str) -> None:
    op.execute(
        "ALTER TABLE credit_transactions DROP CONSTRAINT IF EXISTS credit_transactions_type_check"
    )
    op.execute(
        "ALTER TABLE credit_transactions ADD CONSTRAINT credit_transactions_type_check "
        f"CHECK (type IN ({types}))"
    )


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_entitlements (
            id bigserial PRIMARY KEY,
            tenant_id uuid NOT NULL,
            grant_code text NOT NULL,
            amount_paid_thb numeric(12,2) NOT NULL DEFAULT 0,
            purchased_at timestamptz NOT NULL DEFAULT now(),
            store_limit integer NOT NULL DEFAULT 1,
            cashier_limit integer NOT NULL DEFAULT 3,
            status text NOT NULL DEFAULT 'active'
                CHECK (status IN ('active','revoked','transferred')),
            granted_by uuid,
            transferred_from uuid,
            transferred_to uuid,
            transferred_at timestamptz,
            transferred_by uuid,
            revoked_at timestamptz,
            revoked_by uuid,
            note text,
            updated_at timestamptz NOT NULL DEFAULT now(),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (tenant_id)
        )
        """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_entitlement_code ON pos_entitlements (grant_code)"
    )
    op.execute(_RLS.format(t="pos_entitlements"))
    _widen_ct_check(_CT_TYPES)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pos_entitlements")
    # CHECK 放宽是加性的:若无 pos_buyout 残行则收回;有则保持放宽(收回会违例)。
    op.execute(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM credit_transactions WHERE type = 'pos_buyout') THEN "
        "    ALTER TABLE credit_transactions DROP CONSTRAINT IF EXISTS credit_transactions_type_check; "
        f"    ALTER TABLE credit_transactions ADD CONSTRAINT credit_transactions_type_check CHECK (type IN ({_CT_TYPES_PRE})); "
        "  END IF; "
        "END $$;"
    )
