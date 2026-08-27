# -*- coding: utf-8 -*-
"""会计事务所身份 schema 与经营层分类回填。

accounting_firm_profiles 每行属于一个 f_firm 租户(tenant_id PK),
逻辑上一条 firm 一个 profile。隔离走应用层 WHERE tenant_id(store.py 全带)+ RLS policy
(apply_tenant_rls · 业务连接 SET LOCAL ROLE 后强制)。

Dual-run:alembic/versions/0103_accounting_firm_profiles.py 留档同源 DDL/回填;prod 不跑 alembic,
靠 startup 的 ensure_firm_schema 幂等建(services/startup 独立 firm block)。DFL/回填逐字对齐,
改一处必同改另一处(与 0021/0101 同款内联范式)。

tenant_type_v2 契约:默认改 NULL(未选业态不算类型)· 非空时只许 s_micro/m_business/f_firm。
存量非法值(含 firm/sme/freelancer)按 tenant_modules.__business_type__ 哨兵行重判,已合法三值保留。
"""

from __future__ import annotations

import logging

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

# 业态重判仅作用于待分类或旧非法值的租户，合法三值保留不动。
# 值来自 tenant_modules.module_key='__business_type__' 的 config->>'value'。
# firm=>f_firm;retail/pharmacy/restaurant=>s_micro;service/b2b=>m_business;其余(含无哨兵行)=>NULL。
_BACKFILL_TENANT_TYPE = """
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
    """

# 非空 CHECK 只许三值;NULL 恒通过(未选业态不算类型)。DO 块幂等(无 ADD CONSTRAINT IF NOT EXISTS)。
_CHECK_TENANT_TYPE = """
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
    """

_SEQUENCE = "CREATE SEQUENCE IF NOT EXISTS accounting_firm_profiles_firm_code_seq"

_TABLE = """
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
    """

_BACKFILL_PROFILES = """
    INSERT INTO accounting_firm_profiles (tenant_id, display_name, status)
    SELECT t.id,
           COALESCE(NULLIF(t.display_name, ''), t.name),
           CASE WHEN t.status = 'active' THEN 'active' ELSE 'suspended' END
    FROM tenants t
    WHERE t.tenant_type_v2 = 'f_firm'
    ON CONFLICT (tenant_id) DO NOTHING
    """

_RLS_TABLES = ("accounting_firm_profiles",)


def ensure_firm_schema() -> None:
    """幂等建表 + 回填 + RLS(启动调 · 与 alembic 0103 双跑)。失败 raise· 由 startup 块兜底。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        # 1) tenant_type_v2 默认改 NULL(defensive 补列:确保列在)
        cur.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tenant_type_v2 text")
        cur.execute("ALTER TABLE tenants ALTER COLUMN tenant_type_v2 DROP DEFAULT")
        # 2) 回填:仅非法旧值重判(先于 CHECK,否则非法值炸约束)
        cur.execute(_BACKFILL_TENANT_TYPE)
        # 3) 非空 CHECK 只许三值
        cur.execute(_CHECK_TENANT_TYPE)
        # 4) firm_code 序列 + 表
        cur.execute(_SEQUENCE)
        cur.execute(_TABLE)
        # 5) 只给 f_firm 租户回填 profile
        cur.execute(_BACKFILL_PROFILES)
        # 6) tenant RLS
        apply_tenant_rls(cur, *_RLS_TABLES)
    logger.info("firm schema + tenant_type_v2 分类 + accounting_firm_profiles 已就绪")
