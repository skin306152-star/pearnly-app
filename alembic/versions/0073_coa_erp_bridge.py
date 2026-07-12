# -*- coding: utf-8 -*-
"""科目桥专表 coa_erp_bridge:影子 coa_preset 科目码 ↔ ERP GL 实际科目码。

Revision ID: 0073_coa_erp_bridge
Revises: 0072_client_payroll
Create Date: 2026-07-13

T4a(科目桥做实)。F2 对平此前借 erp_account_mappings「恰填成科目码」的过渡启发式建桥
(shadow_gl_recon 注释明令替换),本表是正式承载:coa_code=coa_preset 27 科目码,
erp_code=GL 上传件里的实际科目码(MR.ERP 扁平 1113-01 样式;Express 四段码不进 join 键)。
按账套隔离(每客户各一套 ERP 账),纯 tenant RLS 照 0072 先例。
Dual-run:services/accounting/bridge_schema.ensure_coa_erp_bridge_schema() 跑同一 DDL
(prod 无 alembic 钩子)。
"""

from alembic import op

revision = "0073_coa_erp_bridge"
down_revision = "0072_client_payroll"
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
        CREATE TABLE IF NOT EXISTS coa_erp_bridge (
            tenant_id           uuid    NOT NULL,
            workspace_client_id bigint  NOT NULL,
            erp_type            text    NOT NULL,
            coa_code            text    NOT NULL,
            erp_code            text    NOT NULL,
            erp_name            text    NOT NULL DEFAULT '',
            match_source        text    NOT NULL DEFAULT 'manual',
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, workspace_client_id, erp_type, coa_code)
        )
        """)
    op.execute(_RLS.format(t="coa_erp_bridge"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS coa_erp_bridge")
