"""商户采购:expense_categories(两级)+ purchase_settings + intake_items + purchase_attachments。

Revision ID: 0033_purchase_config
Revises: 0032_purchase_docs
Create Date: 2026-06-08

费用科目两级(parent_id NULL=大类)· AI 归类映射到子类。预设科目按 (tenant,ws) 懒种子
(services/purchase/categories 首次读时插入,迁移只建表)。采购设置一套账一行。intake_items
存 AI 拿不准的待归类(绝不静默丢错)。purchase_attachments 挂票图 + 系统生成凭据
(替代收据/扣缴凭证 generated=true)。隔离=应用层 WHERE tenant_id;ENABLE RLS 兜底。
Dual-run:services/purchase/schema.ensure_purchase_schema() 同源幂等 DDL。
"""

from alembic import op

revision = "0033_purchase_config"
down_revision = "0032_purchase_docs"
branch_labels = None
depends_on = None

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
        CREATE TABLE IF NOT EXISTS expense_categories (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            parent_id uuid REFERENCES expense_categories (id) ON DELETE CASCADE,
            name text NOT NULL,
            is_active boolean NOT NULL DEFAULT TRUE,
            sort int NOT NULL DEFAULT 0,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_expense_categories_ws "
        "ON expense_categories (tenant_id, workspace_client_id)"
    )
    op.execute(_RLS.format(t="expense_categories"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS purchase_settings (
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            default_vat_rate numeric(5,2) NOT NULL DEFAULT 7,
            auto_stock_in boolean NOT NULL DEFAULT FALSE,
            dedupe_block boolean NOT NULL DEFAULT TRUE,
            default_due_days int NOT NULL DEFAULT 0,
            pay_needs_approval boolean NOT NULL DEFAULT FALSE,
            default_wht_service_rate numeric(5,2) NOT NULL DEFAULT 3,
            base_currency text NOT NULL DEFAULT 'THB',
            updated_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, workspace_client_id)
        )
        """)
    op.execute(_RLS.format(t="purchase_settings"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS intake_items (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            source text,
            raw jsonb,
            image_url text,
            ai_guess jsonb,
            status text NOT NULL DEFAULT 'pending',
            resolved_doc_id uuid,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_intake_items_ws "
        "ON intake_items (tenant_id, workspace_client_id, status)"
    )
    op.execute(_RLS.format(t="intake_items"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS purchase_attachments (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            purchase_doc_id uuid NOT NULL
                REFERENCES purchase_docs (id) ON DELETE CASCADE,
            kind text NOT NULL,
            url text,
            generated boolean NOT NULL DEFAULT FALSE,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_purchase_attachments_doc "
        "ON purchase_attachments (tenant_id, purchase_doc_id)"
    )
    op.execute(_RLS.format(t="purchase_attachments"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS purchase_attachments")
    op.execute("DROP TABLE IF EXISTS intake_items")
    op.execute("DROP TABLE IF EXISTS purchase_settings")
    op.execute("DROP TABLE IF EXISTS expense_categories")
