# -*- coding: utf-8 -*-
"""Daily 周记账应用建表(邀请制 · 每用户独立租户隔离)。

Revision ID: 0101_daily_entries
Revises: 0100_ai_usage_attribution
Create Date: 2026-08-15

pearnly.com/daily 个人收入/支出记录应用:每行属于一个租户(每受邀用户经
create_owner_user 建号得独立租户),RLS 按 tenant 隔离。

Dual-run:prod 无自动迁移钩子,真正建表靠启动幂等自愈
(services/startup.boot_ensures → services.daily.schema.ensure_daily_tables),
RLS policy 靠 services/rls_boot → services.daily.schema.ensure_daily_rls,
本版仅留档。alembic 须 standalone —— 与本文件对应的幂等 DDL 与 policy 谓词
(services/daily/schema._DDL · core/rls._TPL["tenant"])逐字一致,两处都改时
必须同步(与 0021_tenant_modules 同款内联范式)。
"""

from alembic import op

revision = "0101_daily_entries"
down_revision = "0100_ai_usage_attribution"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS daily_entries (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            entry_date date NOT NULL,
            kind text NOT NULL CHECK (kind IN ('income', 'expense')),
            title text NOT NULL,
            amount numeric(12, 2) NOT NULL CHECK (amount > 0),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_daily_entries_tenant_date "
        "ON daily_entries (tenant_id, entry_date)"
    )
    op.execute("ALTER TABLE daily_entries ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON daily_entries FOR ALL "
        "USING ("
        " tenant_id::text = current_setting('app.current_tenant_id', true)"
        " OR current_setting('app.bypass_rls', true) = 'on'"
        ") WITH CHECK ("
        " tenant_id::text = current_setting('app.current_tenant_id', true)"
        " OR current_setting('app.bypass_rls', true) = 'on'"
        ")"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS daily_entries")
