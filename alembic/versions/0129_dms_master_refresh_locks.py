"""Coalesce tenant-scoped DMS master refreshes."""

from alembic import op

revision = "0129_dms_master_refresh_locks"
down_revision = "0128_work_bridge"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS dms_master_refresh_locks (
            scope_key text PRIMARY KEY,
            owner uuid NOT NULL,
            lease_until timestamptz NOT NULL,
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """)
    op.execute("ALTER TABLE dms_master_refresh_locks ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON dms_master_refresh_locks FROM PUBLIC")


def downgrade():
    op.execute("DROP TABLE IF EXISTS dms_master_refresh_locks")
