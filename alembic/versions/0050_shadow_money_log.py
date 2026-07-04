"""shadow_money_log:影子双跑 B 档钱字段 vs 3.5 后台复核比对台账 + 租户 RLS。

prod 无 alembic 钩子,真实建表走 shadow_money_store.ensure_table() 首用自愈;
本文件为文档/双跑对齐,必须 standalone —— 内联同款 DDL + RLS(不 import 运行时 helper)。
"""

from alembic import op

revision = "0050_shadow_money_log"
down_revision = "0049_ocr_cost_log_engine_columns"
branch_labels = None
depends_on = None

_RLS = """
    ALTER TABLE shadow_money_log ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON shadow_money_log;
    CREATE POLICY tenant_isolation ON shadow_money_log
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
        CREATE TABLE IF NOT EXISTS shadow_money_log (
            id bigserial PRIMARY KEY,
            tenant_id uuid NOT NULL,
            history_id text NOT NULL,
            b_total numeric, s_total numeric, total_match boolean,
            b_vat numeric, s_vat numeric, vat_match boolean,
            b_discount numeric, s_discount numeric, discount_match boolean,
            b_subtotal numeric, s_subtotal numeric, subtotal_match boolean,
            match_all boolean,
            b_confidence text,
            status text NOT NULL DEFAULT 'ok',
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_shadow_money_created ON shadow_money_log (created_at)"
    )
    op.execute(_RLS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS shadow_money_log")
