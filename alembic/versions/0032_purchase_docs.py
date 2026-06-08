"""商户采购:purchase_docs + purchase_lines(进项单据头/明细 · docs/purchasing/01)。

Revision ID: 0032_purchase_docs
Revises: 0031_suppliers
Create Date: 2026-06-08

进项票 / 采购单 / 费用三类同表(doc_kind 区分)。钱字段全 numeric(Decimal),含 WHT 预扣税
/ rounding 凑整 / net_payable 实付 / 多币种(currency+fx_rate)/ item_type 商品|服务 / 两级科目。
dedupe_key 防重复抵扣(同税号+单号+合计 → 唯一)。明细行带 tenant_id 冗余 + 经 purchase_doc_id
归属(隔离查询按 tenant_id + doc_id)。隔离=应用层 WHERE tenant_id;ENABLE RLS 兜底。
Dual-run:services/purchase/schema.ensure_purchase_schema() 同源幂等 DDL。
"""

from alembic import op

revision = "0032_purchase_docs"
down_revision = "0031_suppliers"
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
        CREATE TABLE IF NOT EXISTS purchase_docs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            doc_kind text NOT NULL,
            supplier_id uuid,
            doc_no text,
            doc_date date,
            has_vat boolean NOT NULL DEFAULT FALSE,
            currency text NOT NULL DEFAULT 'THB',
            fx_rate numeric(14,6) NOT NULL DEFAULT 1,
            subtotal numeric(14,2) NOT NULL DEFAULT 0,
            discount_total numeric(14,2) NOT NULL DEFAULT 0,
            vat_amount numeric(14,2) NOT NULL DEFAULT 0,
            wht_amount numeric(14,2) NOT NULL DEFAULT 0,
            rounding numeric(14,2) NOT NULL DEFAULT 0,
            grand_total numeric(14,2) NOT NULL DEFAULT 0,
            net_payable numeric(14,2) NOT NULL DEFAULT 0,
            category_id uuid,
            requester text,
            requester_user_id uuid,
            approval_status text NOT NULL DEFAULT 'none',
            payment_status text NOT NULL DEFAULT 'unpaid',
            paid_amount numeric(14,2) NOT NULL DEFAULT 0,
            due_date date,
            source text,
            ocr_raw jsonb,
            dedupe_key text,
            status text NOT NULL DEFAULT 'draft',
            created_by uuid,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_purchase_docs_ws "
        "ON purchase_docs (tenant_id, workspace_client_id)"
    )
    # 防重复抵扣:同套账内 dedupe_key 唯一(NULL 不参与)。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_purchase_docs_dedupe "
        "ON purchase_docs (tenant_id, workspace_client_id, dedupe_key) "
        "WHERE dedupe_key IS NOT NULL"
    )
    op.execute(_RLS.format(t="purchase_docs"))

    op.execute("""
        CREATE TABLE IF NOT EXISTS purchase_lines (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            purchase_doc_id uuid NOT NULL
                REFERENCES purchase_docs (id) ON DELETE CASCADE,
            line_no int NOT NULL DEFAULT 1,
            item_type text NOT NULL DEFAULT 'goods',
            product_id uuid,
            description text,
            qty numeric(14,3) NOT NULL DEFAULT 0,
            unit text,
            unit_price numeric(14,2) NOT NULL DEFAULT 0,
            discount numeric(14,2) NOT NULL DEFAULT 0,
            line_total numeric(14,2) NOT NULL DEFAULT 0,
            vat_rate numeric(5,2) NOT NULL DEFAULT 7,
            vat_applicable boolean NOT NULL DEFAULT TRUE,
            wht_rate numeric(5,2) NOT NULL DEFAULT 0,
            category_id uuid,
            subcategory_id uuid,
            batch_no text,
            expiry_date date
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_purchase_lines_doc "
        "ON purchase_lines (tenant_id, purchase_doc_id)"
    )
    op.execute(_RLS.format(t="purchase_lines"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS purchase_lines")
    op.execute("DROP TABLE IF EXISTS purchase_docs")
