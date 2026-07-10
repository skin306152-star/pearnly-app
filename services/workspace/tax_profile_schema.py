# -*- coding: utf-8 -*-
"""客户税务画像 schema 双跑入口(启动调一次 · 与 alembic 0064 同源幂等 DDL)。

prod 无自动迁移钩子 → startup 经 ensure_tax_profile_schema() 幂等建 4 表 + RLS policy +
defs seed(alembic/versions/0064_client_tax_profile.py 留档)。DDL 与迁移逐字对齐
(改一处必同改两处 · tests/unit/test_tax_profile_schema.py 静态守)。失败仅告警不
raise(不挡主服务)。tax_obligation_defs 是全租户共享法定常量表,不进 RLS 清单。
"""

from __future__ import annotations

from core.rls import apply_tenant_rls

_TABLES = (
    """
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
    """,
    """
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
    """,
    """
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
    """,
    """
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
    """,
)

_INDEXES = (
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_client_alias_norm "
    "ON client_name_aliases (tenant_id, alias_norm) WHERE is_active",
    "CREATE INDEX IF NOT EXISTS ix_client_alias_ws "
    "ON client_name_aliases (tenant_id, workspace_client_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_period_obligation "
    "ON client_period_obligations (tenant_id, workspace_client_id, period, obligation_code)",
    "CREATE INDEX IF NOT EXISTS ix_period_obligation_due "
    "ON client_period_obligations (tenant_id, due_efiling)",
)

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

# tax_obligation_defs 无 tenant 列,不进 RLS 清单(全租户共享法定常量 · 读多写少)。
_RLS_TABLES = (
    "client_tax_profiles",
    "client_name_aliases",
    "client_period_obligations",
)


def ensure_tax_profile_schema() -> None:
    """幂等建税务画像 4 表 + 索引 + RLS + defs seed(startup 调 · 与 alembic 0064 双跑)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        for ddl in _TABLES:
            cur.execute(ddl)
        for idx in _INDEXES:
            cur.execute(idx)
        cur.execute(_SEED_DEFS)
        apply_tenant_rls(cur, *_RLS_TABLES)
