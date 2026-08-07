# -*- coding: utf-8 -*-
"""商品收发存报表(Stock Card)期初结存表。

Revision ID: 0097_stock_card_openings
Revises: 0096_tax_profile_field_meta
Create Date: 2026-08-07

期初口径已拍板(桌面语料评审 · stock-card-report-pending):①期初一次性填表 ②负库存照实
显示 ③进不了账的票单列「未入账清单」。本表只记期初余额(qty/unit_cost/as_of_date),期间
流水直接读 purchase_lines/sales_document_lines 现算移动加权平均,不另建流水表(单一事实源
仍是原始票据,报表口径改了不必回填历史流水)。

归组双轨(services/stockcard/grouping.py):product_id 非空 = 挂到商品主档;否则 name_key
(services/purchase/item_name.clean 清洗后的品名)当归组身份 —— 两者恰一非空(CHECK),
各自一条 partial unique 防重复期初。

纯 tenant RLS:仓库实证 apply_tenant_workspace_rls 虽存在(core/rls.py)但零表采用,
workspace 隔离交给应用层 WHERE tenant_id+workspace_client_id 才是真正隔离主力(0059/0064
同款先例)。Dual-run:services/stockcard/schema.ensure_stock_card_schema() 跑同一 DDL
(prod 无自动迁移钩子,真正建表靠 startup 幂等自愈)。
"""

from alembic import op

revision = "0097_stock_card_openings"
down_revision = "0096_tax_profile_field_meta"
branch_labels = None
depends_on = None

# 与 core.rls._TPL["tenant"] 同源(迁移须 standalone 不 import 应用代码 · 故内联同样谓词)。
_RLS = """
    ALTER TABLE stock_card_openings ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON stock_card_openings;
    CREATE POLICY tenant_isolation ON stock_card_openings
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
        CREATE TABLE IF NOT EXISTS stock_card_openings (
            id bigserial PRIMARY KEY,
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            product_id uuid,
            name_key text,
            qty numeric(14,3) NOT NULL,
            unit_cost numeric(14,2) NOT NULL,
            as_of_date date NOT NULL,
            created_by uuid,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_stock_card_openings_identity CHECK (
                (product_id IS NOT NULL AND name_key IS NULL) OR
                (product_id IS NULL AND name_key IS NOT NULL)
            )
        )
        """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_card_openings_product "
        "ON stock_card_openings (tenant_id, workspace_client_id, product_id) "
        "WHERE product_id IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_card_openings_name "
        "ON stock_card_openings (tenant_id, workspace_client_id, name_key) "
        "WHERE name_key IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_stock_card_openings_ws "
        "ON stock_card_openings (tenant_id, workspace_client_id)"
    )
    op.execute(_RLS)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS stock_card_openings")
