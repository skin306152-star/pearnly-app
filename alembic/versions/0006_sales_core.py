"""Sales (output-VAT) core schema: products, sales documents, numbering, e-Tax placeholders.

Revision ID: 0006_sales_core
Revises: 0005_invoice_risk_checks
Create Date: 2026-06-06

Phase 1 of the sales module (docs/sales-module/docs/13 · PO-1). Creates the
decision-independent core plus the e-Tax forward-compat placeholders.

Type calibration against the live schema (verified, not from the sandbox draft):
  - tenant_id is uuid; money is numeric(14,2); timestamps are timestamptz (UTC).
  - client_id references clients.id, which is BIGSERIAL -> BIGINT here (the draft's
    UUID was a placeholder and would not satisfy the FK).
  - category_id is a nullable BIGINT without an enforced FK: products have no
    dedicated category table yet (supplier_categories is OCR-only), so the link is
    deferred rather than pointed at the wrong table.

Row-level isolation follows the repo convention, NOT a policy block in this
migration: every table carries tenant_id and is read through db.get_cursor_rls
(sets app.current_tenant_id) plus DAL `WHERE tenant_id = %s` filtering, exactly
as the knowledge tables do. Postgres RLS policies are only toggled by the admin
self-test harness in core/db.py.

Table and index names are written literally: a migration is a fixed historical
snapshot and must not shift if a constant is later renamed.
"""

from alembic import op

revision = "0006_sales_core"
down_revision = "0005_invoice_risk_checks"
branch_labels = None
depends_on = None

_TABLES = (
    "etax_submissions",
    "etax_channel_settings",
    "sales_document_lines",
    "sales_documents",
    "document_number_sequences",
    "products",
)


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       uuid NOT NULL,
            code            text,
            barcode         text,
            qr_payload      text,
            name_th         text NOT NULL,
            name_en         text,
            name_zh         text,
            unit            text,
            unit_price      numeric(14,2) NOT NULL DEFAULT 0,
            vat_applicable  boolean NOT NULL DEFAULT true,
            image_url       text,
            category_id     bigint,
            is_active       boolean NOT NULL DEFAULT true,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_products_tenant_code "
        "ON products (tenant_id, code) WHERE code IS NOT NULL"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_tenant ON products (tenant_id, is_active)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_barcode "
        "ON products (tenant_id, barcode) WHERE barcode IS NOT NULL"
    )

    # Thai tax-invoice numbers must not skip: issuing takes a number inside a
    # transaction (SELECT ... FOR UPDATE then +1). Drafts do not consume a number.
    op.execute("""
        CREATE TABLE IF NOT EXISTS document_number_sequences (
            tenant_id    uuid NOT NULL,
            doc_type     text NOT NULL,
            prefix       text NOT NULL,
            period       text NOT NULL,
            next_number  bigint NOT NULL DEFAULT 1,
            PRIMARY KEY (tenant_id, doc_type, prefix, period)
        )
        """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS sales_documents (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       uuid NOT NULL,
            doc_type        text NOT NULL,
            doc_number      text,
            client_id       bigint,
            issue_date      date,
            status          text NOT NULL DEFAULT 'draft',
            currency        text NOT NULL DEFAULT 'THB',
            subtotal        numeric(14,2) NOT NULL DEFAULT 0,
            discount_total  numeric(14,2) NOT NULL DEFAULT 0,
            vat_rate        numeric(5,2)  NOT NULL DEFAULT 7.00,
            vat_amount      numeric(14,2) NOT NULL DEFAULT 0,
            wht_amount      numeric(14,2) NOT NULL DEFAULT 0,
            grand_total     numeric(14,2) NOT NULL DEFAULT 0,
            issued_at       timestamptz,
            created_by      uuid,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_doc_number "
        "ON sales_documents (tenant_id, doc_type, doc_number) WHERE doc_number IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_docs_tenant_status "
        "ON sales_documents (tenant_id, status, issue_date DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_docs_client "
        "ON sales_documents (tenant_id, client_id)"
    )

    # unit_price/description are copied onto the line so an issued document keeps
    # its values even if the product master is later edited.
    op.execute("""
        CREATE TABLE IF NOT EXISTS sales_document_lines (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       uuid NOT NULL,
            document_id     uuid NOT NULL REFERENCES sales_documents (id) ON DELETE CASCADE,
            line_no         int NOT NULL,
            product_id      uuid,
            description     text NOT NULL,
            qty             numeric(14,3) NOT NULL DEFAULT 1,
            unit_price      numeric(14,2) NOT NULL DEFAULT 0,
            discount        numeric(14,2) NOT NULL DEFAULT 0,
            vat_applicable  boolean NOT NULL DEFAULT true,
            line_total      numeric(14,2) NOT NULL DEFAULT 0
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_lines_doc "
        "ON sales_document_lines (document_id, line_no)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_lines_tenant " "ON sales_document_lines (tenant_id)"
    )

    # e-Tax forward-compat placeholders (docs/12). Phase 1 ships the table and the
    # per-customer channel config so the issue path has a stable hook; the actual
    # submission adapters are wired later when a certificate/provider is chosen.
    op.execute("""
        CREATE TABLE IF NOT EXISTS etax_submissions (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id     uuid NOT NULL,
            document_id   uuid NOT NULL REFERENCES sales_documents (id) ON DELETE CASCADE,
            channel       text NOT NULL,
            rd_ref        text,
            status        text NOT NULL DEFAULT 'pending',
            receipt_url   text,
            payload       jsonb,
            error         text,
            submitted_at  timestamptz,
            created_at    timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_etax_submissions_doc "
        "ON etax_submissions (tenant_id, document_id)"
    )

    # Per (tenant, client) channel selection. client_id NULL = tenant default.
    # credentials_ref points at an encrypted secret (core/kms_helper), never the
    # raw certificate.
    op.execute("""
        CREATE TABLE IF NOT EXISTS etax_channel_settings (
            tenant_id        uuid NOT NULL,
            client_id        bigint,
            channel          text NOT NULL DEFAULT 'noop',
            credentials_ref  text,
            config           jsonb,
            created_at       timestamptz NOT NULL DEFAULT now(),
            updated_at       timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_etax_channel_tenant_client "
        "ON etax_channel_settings (tenant_id, COALESCE(client_id, -1))"
    )


def downgrade() -> None:
    for table in _TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
