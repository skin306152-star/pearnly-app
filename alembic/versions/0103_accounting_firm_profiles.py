# -*- coding: utf-8 -*-
"""会计事务所身份与 tenant_type_v2 经营层分类。

Revision ID: 0103_accounting_firm_profiles
Revises: 0102_line_dms_login_tickets
Create Date: 2026-08-27

把 tenants.tenant_type_v2 收敛到 s_micro/m_business/f_firm 三值 +
建 accounting_firm_profiles(每 f_firm 租户一行)· firm_code 走 sequence + DEFAULT 生成
PF 8 位人类码(00000001 起步)。

Dual-run:prod 无 alembic 钩子,真正建表/回填靠启动幂等自愈
(services/startup 独立 firm block → services/firm/schema.ensure_firm_schema),
本版仅留档。alembic 须 standalone —— 与本文件对应的幂等 DDL/回填
(services/firm/schema.__docstring 所列各语句)逐字一致,改一处必同改另一处。
RLS 走 tenant policy(与 0101 同款内联谓词;startup 侧经 apply_tenant_rls 同步)。
"""

from alembic import op

revision = "0103_accounting_firm_profiles"
down_revision = "0102_line_dms_login_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) tenant_type_v2 默认改 NULL(defensive 补列:确保列在)
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tenant_type_v2 text")
    op.execute("ALTER TABLE tenants ALTER COLUMN tenant_type_v2 DROP DEFAULT")
    # 2) 回填:仅非法旧值(含 firm/sme/freelancer)重判 · 已合法三值保留
    op.execute("""
        UPDATE tenants t
        SET tenant_type_v2 = (
            SELECT CASE
                WHEN tm.config->>'value' = 'firm' THEN 'f_firm'
                WHEN tm.config->>'value' IN ('retail', 'pharmacy', 'restaurant') THEN 's_micro'
                WHEN tm.config->>'value' IN ('service', 'b2b') THEN 'm_business'
                ELSE NULL
            END
            FROM tenant_modules tm
            WHERE tm.tenant_id = t.id AND tm.module_key = '__business_type__'
        )
        WHERE t.tenant_type_v2 IS NULL
           OR t.tenant_type_v2 NOT IN ('s_micro', 'm_business', 'f_firm')
        """)
    # 3) 非空 CHECK 只许三值(NULL 恒通过)· DO 块幂等
    op.execute("""
        DO $firm$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_tenants_tenant_type_v2_allowed'
                  AND conrelid = 'tenants'::regclass
            ) THEN
                ALTER TABLE tenants
                    ADD CONSTRAINT ck_tenants_tenant_type_v2_allowed
                    CHECK (tenant_type_v2 IN ('s_micro', 'm_business', 'f_firm'));
            END IF;
        END
        $firm$
        """)
    # 4) firm_code 序列 + 表
    op.execute("CREATE SEQUENCE IF NOT EXISTS accounting_firm_profiles_firm_code_seq")
    op.execute("""
        CREATE TABLE IF NOT EXISTS accounting_firm_profiles (
            tenant_id uuid PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
            firm_code text NOT NULL UNIQUE
                DEFAULT ('PF' || lpad(nextval('accounting_firm_profiles_firm_code_seq')::text, 8, '0')),
            display_name text NOT NULL,
            tax_id text,
            status text NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'suspended')),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    # 5) 只给 f_firm 租户回填 profile；非 active 租户初始为 suspended
    op.execute("""
        INSERT INTO accounting_firm_profiles (tenant_id, display_name, status)
        SELECT t.id,
               COALESCE(NULLIF(t.display_name, ''), t.name),
               CASE WHEN t.status = 'active' THEN 'active' ELSE 'suspended' END
        FROM tenants t
        WHERE t.tenant_type_v2 = 'f_firm'
        ON CONFLICT (tenant_id) DO NOTHING
        """)
    # 6) tenant RLS(内联同款谓词 · 与 apply_tenant_rls 一致)
    op.execute("ALTER TABLE accounting_firm_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON accounting_firm_profiles")
    op.execute(
        "CREATE POLICY tenant_isolation ON accounting_firm_profiles FOR ALL "
        "USING ("
        " tenant_id::text = current_setting('app.current_tenant_id', true)"
        " OR current_setting('app.bypass_rls', true) = 'on'"
        ") WITH CHECK ("
        " tenant_id::text = current_setting('app.current_tenant_id', true)"
        " OR current_setting('app.bypass_rls', true) = 'on'"
        ")"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON accounting_firm_profiles")
    op.execute("DROP TABLE IF EXISTS accounting_firm_profiles")
    op.execute("DROP SEQUENCE IF EXISTS accounting_firm_profiles_firm_code_seq")
    op.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS ck_tenants_tenant_type_v2_allowed")
