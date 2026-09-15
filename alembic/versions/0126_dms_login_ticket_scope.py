"""DMS login tickets: bind each ticket to the issuing OA and binding epoch.

Revision ID: 0126_dms_login_ticket_scope
Revises: 0125_dms_multi_line_oa
Create Date: 2026-09-09

Multi-OA tickets must not survive an OA change or be redeemable by another OA. Existing rows get
``channel_key='dms'`` (legacy OA) and ``binding_id=NULL``; the portal accepts a NULL epoch only
for a legacy binding, so an old ticket can never authorize an A/B binding.

Dual-run: ``services/line_dms/login_tickets.ensure_table()`` runs the same idempotent DDL. The
release schema job (``services.cloud_runtime.schema.migrate``) calls the startup schema block that
includes this module, so the columns exist before the revision receives traffic.
"""

from alembic import op

revision = "0126_dms_login_ticket_scope"
down_revision = "0125_dms_multi_line_oa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE line_dms_login_tickets "
        "ADD COLUMN IF NOT EXISTS channel_key text NOT NULL DEFAULT 'dms'"
    )
    op.execute("ALTER TABLE line_dms_login_tickets ADD COLUMN IF NOT EXISTS binding_id uuid")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_line_dms_login_tickets_scope "
        "ON line_dms_login_tickets (tenant_id, channel_key, user_id)"
    )


def downgrade() -> None:
    raise RuntimeError(
        "DMS login ticket OA scope cannot be dropped without losing the ticket audit trail"
    )
