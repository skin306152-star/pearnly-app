"""Invoice delivery: send log, share token, seller email (docs/16 §L5 / PO-7).

Revision ID: 0018_sales_send
Revises: 0017_sales_settings
Create Date: 2026-06-06

PO-7 send: an issued invoice can be delivered to the buyer. This adds the pieces the send path
needs, channel-agnostic:
  - sales_documents.share_token: an unguessable capability token for a public PDF link (the LINE
    "I forward it myself" flow — the seller forwards the link from their own LINE; also reusable
    for any link-based share). Generated on demand, reused after.
  - workspace_clients.email: the seller's reply address, used as Reply-To so a buyer replying to
    the official-relay email reaches the seller, not hello@pearnly.com.
  - sales_document_sends: a delivery log (one row per attempt) — channel/identity/recipient/status.

All nullable / additive -> backward compatible. Isolation app-layer (get_cursor_rls + WHERE
tenant_id); the share-token lookup runs bypass-RLS because a public link carries no tenant context
(the secret token is the capability). Names written literally (a migration is a fixed snapshot).
"""

from alembic import op

revision = "0018_sales_send"
down_revision = "0017_sales_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE sales_documents ADD COLUMN IF NOT EXISTS share_token text")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_doc_share_token "
        "ON sales_documents (share_token) WHERE share_token IS NOT NULL"
    )
    op.execute("ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS email text")
    op.execute("""
        CREATE TABLE IF NOT EXISTS sales_document_sends (
            id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id    uuid NOT NULL,
            document_id  uuid NOT NULL REFERENCES sales_documents (id) ON DELETE CASCADE,
            channel      text NOT NULL,
            identity     text NOT NULL,
            recipient    text,
            status       text NOT NULL DEFAULT 'sent',
            error        text,
            created_by   uuid,
            created_at   timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sales_sends_doc "
        "ON sales_document_sends (tenant_id, document_id, created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sales_document_sends")
    op.execute("ALTER TABLE workspace_clients DROP COLUMN IF EXISTS email")
    op.execute("DROP INDEX IF EXISTS uq_sales_doc_share_token")
    op.execute("ALTER TABLE sales_documents DROP COLUMN IF EXISTS share_token")
