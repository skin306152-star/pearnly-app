"""DMS multi-OA: per-account LINE OA assignment + channel-scoped bindings/codes/sessions.

Revision ID: 0125_dms_multi_line_oa
Revises: 0124_stocktake_scan_entries
Create Date: 2026-09-08

Each DMS account (tenant-first subject) can run on one of several LINE OAs that share the
Pearnly provider. Bindings, 6-digit bind codes and conversation sessions carry ``channel_key``
so the same LINE user id can never be matched across OAs, and the Earn page can change an
account's OA without leaving stale bindings answering on the old OA.

Dual-run: services/line_dms/schema.ensure_tables() runs the same DDL from the Cloud Run schema
job (services.cloud_runtime.schema.migrate → services.startup._boot_schema_ddl); this file is the
reviewed record for that step, not the mechanism that applies it.
"""

from alembic import op

revision = "0125_dms_multi_line_oa"
down_revision = "0124_stocktake_scan_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE line_dms_bindings "
        "ADD COLUMN IF NOT EXISTS channel_key text NOT NULL DEFAULT 'dms'"
    )
    op.execute(
        "ALTER TABLE line_dms_binding_codes "
        "ADD COLUMN IF NOT EXISTS channel_key text NOT NULL DEFAULT 'dms'"
    )
    op.execute(
        "ALTER TABLE dms_line_sessions "
        "ADD COLUMN IF NOT EXISTS channel_key text NOT NULL DEFAULT 'dms'"
    )
    op.execute(
        "ALTER TABLE line_dms_bindings DROP CONSTRAINT IF EXISTS line_dms_bindings_line_user_id_key"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_line_dms_bindings_channel_line "
        "ON line_dms_bindings (channel_key, line_user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_line_dms_bindings_user ON line_dms_bindings (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_line_dms_bindings_tenant ON line_dms_bindings (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_line_dms_binding_codes_user "
        "ON line_dms_binding_codes (user_id)"
    )
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'dms_line_sessions'::regclass
                  AND contype = 'p'
                  AND pg_get_constraintdef(oid) NOT LIKE '%channel_key%'
            ) THEN
                ALTER TABLE dms_line_sessions DROP CONSTRAINT dms_line_sessions_pkey;
                ALTER TABLE dms_line_sessions
                    ADD PRIMARY KEY (tenant_id, channel_key, line_user_id);
            END IF;
        END $$;
        """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS dms_account_line_channels (
            subject_id text PRIMARY KEY,
            channel_key text NOT NULL,
            updated_at timestamptz DEFAULT now(),
            updated_by uuid
        )
        """)


def downgrade() -> None:
    raise RuntimeError(
        "DMS multi-OA schema rollback needs review; channel assignments must be kept"
    )
