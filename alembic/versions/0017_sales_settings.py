"""Tenant sales settings + buyer-directory fields on clients (docs/16 §M7 / §N).

Revision ID: 0017_sales_settings
Revises: 0016_sales_seller_brand
Create Date: 2026-06-06

Until now numbering / approval / price-inclusive were per-request only; there was no tenant
default store. `sales_settings` (one row per tenant) holds those defaults: numbering
prefix/reset/start (start seeds a fresh sequence to continue a legacy book), approval_mode (this
activates the §F workflow), and the create-form defaults (price-inclusive / WHT / template / lang /
paper / copies layout). The issue path reads it; a document may still override per request.

`clients` gets buyer-directory fields (party_type / branch / promptpay_id) so a saved client can
prefill the buyer block (docs/15). Columns added here; the clients CRUD write path is wired with
the PO-10 客户管理 screen.

All nullable / defaulted -> backward compatible. Isolation app-layer (get_cursor_rls + WHERE
tenant_id); names written literally (a migration is a fixed snapshot).
"""

from alembic import op

revision = "0017_sales_settings"
down_revision = "0016_sales_seller_brand"
branch_labels = None
depends_on = None

_CLIENT_COLUMNS = ("party_type", "branch", "promptpay_id")


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS sales_settings (
            tenant_id                  uuid PRIMARY KEY,
            number_prefix              text,
            number_reset               text    NOT NULL DEFAULT 'yearly',
            number_start               bigint  NOT NULL DEFAULT 1,
            approval_mode              text    NOT NULL DEFAULT 'none',
            price_includes_vat_default boolean NOT NULL DEFAULT false,
            default_wht_rate           numeric(6,2) NOT NULL DEFAULT 0,
            default_template_id        text    NOT NULL DEFAULT 'classic',
            default_doc_lang           text    NOT NULL DEFAULT 'th',
            default_paper              text    NOT NULL DEFAULT 'A4',
            default_copies_layout      text    NOT NULL DEFAULT 'separate',
            created_at                 timestamptz NOT NULL DEFAULT now(),
            updated_at                 timestamptz NOT NULL DEFAULT now()
        )
        """)
    for col in _CLIENT_COLUMNS:
        op.execute(f"ALTER TABLE clients ADD COLUMN IF NOT EXISTS {col} text")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sales_settings")
    for col in _CLIENT_COLUMNS:
        op.execute(f"ALTER TABLE clients DROP COLUMN IF EXISTS {col}")
