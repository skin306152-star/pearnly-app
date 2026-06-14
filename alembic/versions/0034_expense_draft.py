"""一句话记账捕获草稿表 expense_draft(LINE 文本/图片路共用 · docs/smart-intake/14)。

Revision ID: 0034_expense_draft
Revises: 0033_purchase_config
Create Date: 2026-06-15

捕获层(金额/分类/卖家/日期),上游于 journal_vouchers(复式过账)——LINE 一句话先落草稿,
用户确认/网页复核后才下推。字段对齐 services/ocr ThaiInvoice,图/文两路共用同一张草稿。
隔离=应用层 WHERE tenant_id + workspace_client_id;ENABLE RLS 兜底。
Dual-run:services/expense/schema.ensure_expense_schema() 同源幂等 DDL(prod 无 alembic 钩子,
走 ensure;本文件留档)。
"""

from alembic import op

revision = "0034_expense_draft"
down_revision = "0033_purchase_config"
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
        CREATE TABLE IF NOT EXISTS expense_draft (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            source text NOT NULL DEFAULT 'line_text',
            status text NOT NULL DEFAULT 'draft',
            line_user_id text,
            raw_text text,
            document_type text NOT NULL DEFAULT '',
            amount numeric(14,2),
            qty numeric(14,3),
            unit_price numeric(14,2),
            currency text NOT NULL DEFAULT 'THB',
            expense_type text NOT NULL DEFAULT '',
            category text NOT NULL DEFAULT '',
            subcategory text NOT NULL DEFAULT '',
            category_id uuid,
            subcategory_id uuid,
            vendor_name text NOT NULL DEFAULT '',
            vendor_tax_id text NOT NULL DEFAULT '',
            invoice_number text NOT NULL DEFAULT '',
            doc_date date,
            vat_mode text NOT NULL DEFAULT 'included',
            vat_amount numeric(14,2),
            wht_amount numeric(14,2),
            note text NOT NULL DEFAULT '',
            confidence numeric(5,2) NOT NULL DEFAULT 0,
            created_by text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_expense_draft_ws_status "
        "ON expense_draft (tenant_id, workspace_client_id, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_expense_draft_invoice_no "
        "ON expense_draft (tenant_id, workspace_client_id, invoice_number)"
    )
    op.execute(_RLS.format(t="expense_draft"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS expense_draft")
