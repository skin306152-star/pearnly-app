# -*- coding: utf-8 -*-
"""客户税务画像:client_tax_profiles + client_name_aliases + 义务 defs/物化 4 表。

Revision ID: 0064_client_tax_profile
Revises: 0063_pos_entitlements
Create Date: 2026-07-10

画像→当期义务生成(《终局画面》§三.1)+ 泰英商号别名(G1R2 毛刺②根治)。
隔离=应用层 WHERE tenant_id + 纯 tenant RLS(0059/0061 同款,tenant_id NOT NULL)。
Dual-run:services/workspace/tax_profile_schema.ensure_tax_profile_schema() 跑同一 DDL。
"""

from alembic import op

revision = "0064_client_tax_profile"
down_revision = "0063_pos_entitlements"
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

# 义务 defs seed(方案 §3.2 九行 · 截止日两轨 + 证据级 · 换版改 seed 不改码)。
_SEED_DEFS = """
    INSERT INTO tax_obligation_defs
        (obligation_code, display_names, trigger_kind, due_paper_day, due_efiling_day,
         sso_epayment_extra_workdays, evidence_level, note, effective_from)
    VALUES
        ('pnd1', '{"zh": "工资薪金预扣税申报(PND1)", "th": "แบบยื่นภาษีเงินได้หัก ณ ที่จ่าย (ภ.ง.ด.1)", "en": "Withholding Tax Return (PND1 - Salary)", "ja": "給与源泉徴収税申告書(PND1)"}'::jsonb,
         'has_employees', 7, 15, 0, 'official',
         '触发=雇员有无(has_employees=yes);unknown→tentative+确认(工资常另做,不硬阻断)',
         DATE '2024-02-01'),
        ('pnd2', '{"zh": "利息股息预扣税申报(PND2)", "th": "แบบยื่นภาษีเงินได้หัก ณ ที่จ่าย (ภ.ง.ด.2)", "en": "Withholding Tax Return (PND2 - Interest/Dividend)", "ja": "利息配当源泉徴収税申告書(PND2)"}'::jsonb,
         'pays_interest_dividend', 7, 15, 0, 'official',
         '触发=向个人付利息/股息(pays_interest_dividend=yes ∪ 数据实测);公告ข้อ1.3明列,首版曾漏已补',
         DATE '2024-02-01'),
        ('pnd3', '{"zh": "个人预扣税申报(PND3)", "th": "แบบยื่นภาษีเงินได้หัก ณ ที่จ่าย (ภ.ง.ด.3)", "en": "Withholding Tax Return (PND3 - Individual)", "ja": "個人源泉徴収税申告書(PND3)"}'::jsonb,
         'pays_individuals', 7, 15, 0, 'official',
         '触发=向个人付款预扣(pays_individuals=yes ∪ 数据见向个人WHT);unknown+数据命中→data_triggered,否则tentative',
         DATE '2024-02-01'),
        ('pnd53', '{"zh": "法人预扣税申报(PND53)", "th": "แบบยื่นภาษีเงินได้หัก ณ ที่จ่าย (ภ.ง.ด.53)", "en": "Withholding Tax Return (PND53 - Juristic)", "ja": "法人源泉徴収税申告書(PND53)"}'::jsonb,
         'pays_juristic', 7, 15, 0, 'official',
         '触发=向法人付款预扣(pays_juristic=yes ∪ 数据见向法人WHT);unknown+数据命中→data_triggered,否则tentative',
         DATE '2024-02-01'),
        ('pnd54', '{"zh": "境外预扣税申报(PND54)", "th": "แบบยื่นภาษีเงินได้หัก ณ ที่จ่าย (ภ.ง.ด.54)", "en": "Withholding Tax Return (PND54 - Foreign)", "ja": "海外源泉徴収税申告書(PND54)"}'::jsonb,
         'pays_foreign', 7, 15, 0, 'official',
         '触发=向境外付款预扣(pays_foreign=yes ∪ 数据见境外付款);联动 PP36(反向征收VAT)',
         DATE '2024-02-01'),
        ('pp36', '{"zh": "反向征收增值税申报(PP36)", "th": "แบบนำส่งภาษีมูลค่าเพิ่ม (ภ.พ.36)", "en": "VAT Remittance Return (PP36)", "ja": "リバースチャージ付加価値税申告書(PP36)"}'::jsonb,
         'pays_foreign', 7, 15, 0, 'official',
         '随 PND54 联动(境外服务反向征收VAT);未知→tentative',
         DATE '2024-02-01'),
        ('pp30', '{"zh": "增值税申报(PP30)", "th": "แบบแสดงรายการภาษีมูลค่าเพิ่ม (ภ.พ.30)", "en": "VAT Return (PP30)", "ja": "付加価値税申告書(PP30)"}'::jsonb,
         'vat_status', 15, 23, 0, 'official',
         'vat_status=registered 恒生成(含零申报);未知VAT态仍生成+确认;dormant→nil',
         DATE '2024-02-01'),
        ('sso', '{"zh": "社保申报(สปส.1-10)", "th": "แบบนำส่งเงินสมทบ (สปส. 1-10)", "en": "Social Security Fund Contribution", "ja": "社会保険料申告(SSO)"}'::jsonb,
         'has_employees', 15, NULL, 7, 'official+portal',
         '随 has_employees;e-Payment 在纸质15日基础上再+7工作日(门户级证据);unknown→tentative',
         DATE '2024-02-01'),
        ('sbt', '{"zh": "特定营业税申报(PND ภ.ธ.40)", "th": "แบบแสดงรายการภาษีธุรกิจเฉพาะ (ภ.ธ.40)", "en": "Specific Business Tax Return (SBT)", "ja": "特定事業税申告書(SBT)"}'::jsonb,
         'sbt_status', 15, NULL, 0, 'supplement',
         'sbt_status=registered 才生成;默认none不生成;行业命中金融/地产等且未确认→挂确认,不默默漏',
         DATE '2024-02-01')
    ON CONFLICT (obligation_code) DO NOTHING
"""


def upgrade() -> None:
    # 1) 画像:每客户一行(PK 天然幂等 upsert)
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_tax_profiles (
            tenant_id               uuid    NOT NULL,
            workspace_client_id     bigint  NOT NULL,
            sbt_status              text    NOT NULL DEFAULT 'none',
            sbt_business_type       text    NOT NULL DEFAULT '',
            has_employees           text    NOT NULL DEFAULT 'unknown',
            pays_individuals        text    NOT NULL DEFAULT 'unknown',
            pays_juristic           text    NOT NULL DEFAULT 'unknown',
            pays_foreign            text    NOT NULL DEFAULT 'unknown',
            pays_interest_dividend  text    NOT NULL DEFAULT 'unknown',
            has_multi_branch        boolean NOT NULL DEFAULT false,
            branch_count            smallint NOT NULL DEFAULT 1,
            filing_disposition      text    NOT NULL DEFAULT 'active',
            efiling_enrolled        text    NOT NULL DEFAULT 'unknown',
            tax_agent_authorized    boolean NOT NULL DEFAULT false,
            tax_agent_ref           text    NOT NULL DEFAULT '',
            vat_credit_carry        numeric(14,2) NOT NULL DEFAULT 0,
            source                  text    NOT NULL DEFAULT 'onboarding',
            confidence              numeric(4,3),
            profile_version         integer NOT NULL DEFAULT 1,
            updated_by              text    NOT NULL DEFAULT 'system',
            updated_at              timestamptz NOT NULL DEFAULT now(),
            created_at              timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, workspace_client_id)
        )
        """)
    op.execute(_RLS.format(t="client_tax_profiles"))
    # vat_status(读 workspace_clients.vat_registered)、has_multi_branch(派生 branch)
    # 不重复存,读时 join——单一事实源。

    # 2) 别名:客户 1:N;同租户 alias_norm 唯一防污染
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_name_aliases (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid    NOT NULL,
            workspace_client_id bigint  NOT NULL,
            alias_raw           text    NOT NULL,
            alias_norm          text    NOT NULL,
            alias_kind          text    NOT NULL DEFAULT 'misc',
            match_mode          text    NOT NULL DEFAULT 'exact',
            source              text    NOT NULL DEFAULT 'onboarding',
            confidence          numeric(4,3),
            is_active           boolean NOT NULL DEFAULT true,
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    # 污染闸①:同租户一个 active norm 只指一个客户(唯一索引即查询索引,免重复建
    # 同列同 WHERE 的非唯一索引)。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_client_alias_norm "
        "ON client_name_aliases (tenant_id, alias_norm) WHERE is_active"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_client_alias_ws "
        "ON client_name_aliases (tenant_id, workspace_client_id)"
    )
    op.execute(_RLS.format(t="client_name_aliases"))

    # 3) 义务定义(参考/seed·截止日不写死·版本化)
    op.execute("""
        CREATE TABLE IF NOT EXISTS tax_obligation_defs (
            obligation_code     text PRIMARY KEY,
            display_names       jsonb NOT NULL DEFAULT '{}'::jsonb,
            trigger_kind        text NOT NULL,
            due_paper_day       smallint,
            due_efiling_day     smallint,
            sso_epayment_extra_workdays smallint NOT NULL DEFAULT 0,
            evidence_level      text NOT NULL DEFAULT '',
            note                text NOT NULL DEFAULT '',
            effective_from      date NOT NULL DEFAULT DATE '2024-02-01',
            effective_to        date,
            version             integer NOT NULL DEFAULT 1
        )
        """)
    # 无 tenant 列:全租户共享的法定日历常量表,RLS 不启用(参考数据,读多写少·仅迁移/超管写)。
    op.execute(_SEED_DEFS)

    # 4) 当期义务物化(工单期×义务码·幂等 upsert);申报/回执列留空给批次 C/D
    op.execute("""
        CREATE TABLE IF NOT EXISTS client_period_obligations (
            id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           uuid   NOT NULL,
            workspace_client_id bigint NOT NULL,
            work_order_id       uuid   REFERENCES work_orders (id) ON DELETE SET NULL,
            period              text   NOT NULL,
            obligation_code     text   NOT NULL,
            status              text   NOT NULL DEFAULT 'tentative',
            trigger_source      text   NOT NULL DEFAULT '',
            due_paper           date,
            due_efiling         date,
            -- 批次 C/D 预留(B1 不填):
            assignee            text,
            filed_at            timestamptz,
            receipt_ref         text,
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_period_obligation "
        "ON client_period_obligations (tenant_id, workspace_client_id, period, obligation_code)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_period_obligation_due "
        "ON client_period_obligations (tenant_id, due_efiling)"
    )
    op.execute(_RLS.format(t="client_period_obligations"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS client_period_obligations")
    op.execute("DROP TABLE IF EXISTS tax_obligation_defs")
    op.execute("DROP TABLE IF EXISTS client_name_aliases")
    op.execute("DROP TABLE IF EXISTS client_tax_profiles")
