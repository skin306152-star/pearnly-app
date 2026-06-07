"""POS 小票:pos_sales + pos_sale_lines + pos_payments(POS 项目 · PO-B2 · docs/pos/03 §4)。

Revision ID: 0025_pos_sales
Revises: 0024_pos_core
Create Date: 2026-06-07

小票头 pos_sales(可离线产生 · client_uuid UNIQUE 幂等防补传双扣)+ 明细 pos_sale_lines
(冻结售卖单位换算系数 unit_factor + 扣库存 qty_base + 退货指回原行 refund_of_line_id)+
混合付 pos_payments(一单多支付)。升级正式税票回填 full_invoice_id→sales_documents。

外键类型对齐现有混合(03 §0/§7):tenant_id/sale_id/cashier_id/shift_id/product_id/batch_id/
full_invoice_id=uuid;workspace_client_id/terminal_id/member_client_id=bigint。钱 numeric(14,2)、
量 numeric(14,3)。隔离=应用层 WHERE tenant_id;ENABLE RLS + policy 兜底。
Dual-run:services/pos/sale.ensure_sales_schema() 跑同一幂等 DDL(prod 无自动迁移)。
"""

from alembic import op

revision = "0025_pos_sales"
down_revision = "0024_pos_core"
branch_labels = None
depends_on = None

_RLS_TABLES = ("pos_sales", "pos_sale_lines", "pos_payments")


def _policy(table: str) -> str:
    return f"""
        CREATE POLICY tenant_isolation ON {table}
        FOR ALL
        USING (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
        WITH CHECK (
            tenant_id::text = current_setting('app.current_tenant_id', true)
            OR current_setting('app.bypass_rls', true) = 'on'
        )
    """


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_sales (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            workspace_client_id bigint NOT NULL,
            client_uuid uuid UNIQUE,
            shift_id uuid REFERENCES pos_shifts(id) ON DELETE SET NULL,
            terminal_id bigint REFERENCES pos_terminals(id) ON DELETE SET NULL,
            cashier_id uuid REFERENCES pos_cashiers(id) ON DELETE SET NULL,
            receipt_no text,
            doc_kind text NOT NULL DEFAULT 'receipt',
            sale_type text NOT NULL DEFAULT 'sale',
            refund_of_sale_id uuid REFERENCES pos_sales(id) ON DELETE SET NULL,
            member_client_id bigint,
            subtotal numeric(14,2) NOT NULL DEFAULT 0,
            discount_total numeric(14,2) NOT NULL DEFAULT 0,
            vat_amount numeric(14,2) NOT NULL DEFAULT 0,
            grand_total numeric(14,2) NOT NULL DEFAULT 0,
            price_includes_vat boolean NOT NULL DEFAULT FALSE,
            paid_total numeric(14,2) NOT NULL DEFAULT 0,
            change_amount numeric(14,2) NOT NULL DEFAULT 0,
            full_invoice_id uuid,
            status text NOT NULL DEFAULT 'completed',
            sold_at timestamptz NOT NULL DEFAULT now(),
            synced_at timestamptz,
            created_by uuid,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_sales_shift "
        "ON pos_sales (tenant_id, workspace_client_id, shift_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_sales_receipt " "ON pos_sales (tenant_id, receipt_no)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_sales_sold_at "
        "ON pos_sales (tenant_id, workspace_client_id, sold_at)"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_sale_lines (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            sale_id uuid NOT NULL REFERENCES pos_sales(id) ON DELETE CASCADE,
            product_id uuid NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
            sell_unit text,
            unit_factor numeric(14,3) NOT NULL DEFAULT 1,
            qty numeric(14,3) NOT NULL,
            qty_base numeric(14,3) NOT NULL,
            unit_price numeric(14,2) NOT NULL,
            line_discount numeric(14,2) NOT NULL DEFAULT 0,
            vat_applicable boolean NOT NULL DEFAULT TRUE,
            batch_id uuid,
            refund_of_line_id uuid REFERENCES pos_sale_lines(id) ON DELETE SET NULL,
            line_total numeric(14,2) NOT NULL
        )
        """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_pos_sale_lines_sale ON pos_sale_lines (sale_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_pos_sale_lines_refund "
        "ON pos_sale_lines (refund_of_line_id)"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS pos_payments (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            sale_id uuid NOT NULL REFERENCES pos_sales(id) ON DELETE CASCADE,
            method text NOT NULL,
            amount numeric(14,2) NOT NULL,
            ref text
        )
        """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_pos_payments_sale ON pos_payments (sale_id)")
    for table in _RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(_policy(table))


def downgrade() -> None:
    for table in reversed(_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute("DROP TABLE IF EXISTS pos_payments")
    op.execute("DROP TABLE IF EXISTS pos_sale_lines")
    op.execute("DROP TABLE IF EXISTS pos_sales")
