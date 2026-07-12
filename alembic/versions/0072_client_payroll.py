# -*- coding: utf-8 -*-
"""工资进料:client_payroll_templates(列映射模板)+ client_payroll_rows(月度进料行)。

Revision ID: 0072_client_payroll
Revises: 0071_pos_client_uuid_scope
Create Date: 2026-07-12

批次 H(ภ.ง.ด.1 工资预扣进料引擎)· 方案 §2.3/P4。列映射模板下月自动套;月度进料行供
ภ.ง.ด.1ก 年度聚合 + 义务追溯。隔离=应用层 WHERE tenant_id + 纯 tenant RLS(0064 同款)。
Dual-run:services/payroll/schema.ensure_payroll_schema() 跑同一 DDL(prod 无 alembic 钩子)。
"""

from alembic import op

revision = "0072_client_payroll"
down_revision = "0071_pos_client_uuid_scope"
branch_labels = None
depends_on = None

# 与 core.rls._TPL["tenant"] 同源(迁移须 standalone 不 import 应用代码 · 内联同款谓词)。
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
        CREATE TABLE IF NOT EXISTS client_payroll_templates (
            tenant_id           uuid    NOT NULL,
            workspace_client_id bigint  NOT NULL,
            column_map          jsonb   NOT NULL DEFAULT '{}'::jsonb,
            income_code         text    NOT NULL DEFAULT '40(1)',
            fixed_values        jsonb   NOT NULL DEFAULT '{}'::jsonb,
            header_hash         text    NOT NULL DEFAULT '',
            updated_at          timestamptz NOT NULL DEFAULT now(),
            created_at          timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, workspace_client_id)
        )
        """)
    op.execute(_RLS.format(t="client_payroll_templates"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS client_payroll_rows (
            id                  bigserial PRIMARY KEY,
            tenant_id           uuid    NOT NULL,
            workspace_client_id bigint  NOT NULL,
            period              text    NOT NULL,
            seq                 integer NOT NULL,
            employee_id         text    NOT NULL,
            title               text    NOT NULL DEFAULT '',
            first_name          text    NOT NULL DEFAULT '',
            last_name           text    NOT NULL DEFAULT '',
            income_code         text    NOT NULL DEFAULT '40(1)',
            paid_date           date,
            paid_amount         numeric(15,2) NOT NULL DEFAULT 0,
            wht_amount          numeric(15,2) NOT NULL DEFAULT 0,
            condition           text    NOT NULL DEFAULT '1',
            created_at          timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_payroll_rows_period "
        "ON client_payroll_rows (tenant_id, workspace_client_id, period)"
    )
    op.execute(_RLS.format(t="client_payroll_rows"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS client_payroll_rows")
    op.execute("DROP TABLE IF EXISTS client_payroll_templates")
