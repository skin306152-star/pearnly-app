"""Dynamic buyer block, party snapshot freeze, and payment status (PO buyer-module + §A/§J).

Revision ID: 0009_sales_buyer_and_payment
Revises: 0008_sales_seller_fields
Create Date: 2026-06-06

Adds to sales_documents:
  - Buyer block columns (docs/sales-module/docs/15): the buyer is no longer just a
    clients FK. A document carries its own buyer type (company/individual/foreigner/
    anonymous), name/address, a single tax_id field whose meaning follows the type
    (company tax id / national id / passport), and a branch marker that only applies
    to company buyers. Editable while draft, immutable once issued (status guard).
  - parties_snapshot jsonb (docs/16 §A): both seller and buyer are frozen here at
    issue time so a re-rendered PDF of an issued document never shifts when the
    clients / workspace_clients masters are later edited. PDF reads the snapshot for
    issued documents and composes live only for draft previews.
  - Payment columns (docs/16 §J): a receipt or combined tax-invoice/receipt must be
    paid before it can be issued; tracked here.

All columns are nullable or defaulted, so the migration is backward compatible.
Isolation stays at the app layer (get_cursor_rls + DAL WHERE tenant_id), matching
0006/0008; no RLS policy block here. Names are written literally (a migration is a
fixed historical snapshot).
"""

from alembic import op

revision = "0009_sales_buyer_and_payment"
down_revision = "0008_sales_seller_fields"
branch_labels = None
depends_on = None

# Buyer block + freeze + payment columns, in drop order for downgrade.
_DOC_COLUMNS = (
    "payment_date",
    "payment_method",
    "paid_amount",
    "payment_status",
    "parties_snapshot",
    "buyer_branch_no",
    "buyer_branch_type",
    "buyer_tax_id",
    "buyer_address",
    "buyer_name",
    "buyer_type",
)


def upgrade() -> None:
    # Buyer block: held on the document (not only via client_id) so anonymous /
    # individual / foreigner buyers that have no clients row can still be invoiced.
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS buyer_type text")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS buyer_name text")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS buyer_address text")
    # One tax_id column for three meanings (company tax id / national id / passport);
    # the label and validation are decided by buyer_type, not by separate columns.
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS buyer_tax_id text")
    # branch marker only meaningful when buyer_type = 'company': 'hq' | 'branch'.
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS buyer_branch_type text")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS buyer_branch_no text")

    # Frozen seller+buyer snapshot written at issue (docs/16 §A). jsonb shape:
    # {"seller": {...}, "buyer": {...}} with name/address/tax_id/branch/phone/type.
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS parties_snapshot jsonb")

    # Payment (docs/16 §J). Receipt / combined doc must be paid before issue.
    op.execute(
        "ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS payment_status text "
        "NOT NULL DEFAULT 'unpaid'"
    )
    op.execute(
        "ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS paid_amount numeric(14,2) "
        "NOT NULL DEFAULT 0"
    )
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS payment_method text")
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS payment_date date")


def downgrade() -> None:
    for col in _DOC_COLUMNS:
        op.execute(f"ALTER TABLE sales_documents DROP COLUMN IF EXISTS {col}")
