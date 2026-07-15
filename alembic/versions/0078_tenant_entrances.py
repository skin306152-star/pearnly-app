# -*- coding: utf-8 -*-
"""授权入口集显式表 tenant_entrances(登录准入单一事实源 · Phase2)。

Revision ID: 0078_tenant_entrances
Revises: 0077_brain_shadow_log
Create Date: 2026-07-16

一租户可持有多个入口(main/pos/ai),(tenant_id, entrance) 一行。Phase1 靠 authorized_entrances
从 business_type/pos 模块/pearnly_ai_m1 名单【推导】;Phase2 升级成读本表,但保留推导为回落
(services/auth/entrance.py 双轨:表缺失/无行/异常 → 走推导)。故本迁移未在 prod 跑之前(prod
不自动迁移),登录行为与 Phase1 逐字节一致;prod 手动 alembic upgrade 建表 + 跑
scripts/backfill_tenant_entrances.py 回填后才切表。发放侧(注册/开 POS/邀请 AI)成功时顺带写本表。

RLS:这是【平台级授权表】(登录时读、超管/注册流写),非租户业务数据 —— 与 platform_setting_allowlist
同款按平台表处理,显式 DISABLE RLS(守门走应用层),不套 tenant_isolation policy。理由:登录读发生在
RLS 租户上下文建立之前,若加 tenant 隔离谓词会在无上下文时过滤成零行(虽 prod 以 BYPASSRLS 连库不受
影响,仍从终态钉死避免 Supabase「RLS 开 + 零 policy = deny-all」孤儿,见 b8-rls-no-policy-orphans)。
"""

from alembic import op

revision = "0078_tenant_entrances"
down_revision = "0077_brain_shadow_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_entrances (
            id bigserial PRIMARY KEY,
            tenant_id uuid NOT NULL,
            entrance text NOT NULL CHECK (entrance IN ('main','pos','ai')),
            granted_at timestamptz NOT NULL DEFAULT now(),
            granted_by text,
            UNIQUE (tenant_id, entrance)
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tenant_entrances_tenant " "ON tenant_entrances (tenant_id)"
    )
    # 平台授权表靠应用层守门,不套 RLS(与 platform_setting_allowlist 同款终态)。
    op.execute("ALTER TABLE tenant_entrances DISABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tenant_entrances")
