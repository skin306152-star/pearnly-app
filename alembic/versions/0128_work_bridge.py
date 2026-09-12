"""Universal COWORK / WeKan identity handoff and member provisioning."""

from alembic import op
from services.work_bridge.schema import TABLES

revision = "0128_work_bridge"
down_revision = "0127_stocktake_photos"
branch_labels = None
depends_on = None


def upgrade():
    for name, ddl in TABLES.items():
        op.execute(ddl)
        op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {name}")
        predicate = (
            "tenant_id::text = current_setting('app.current_tenant_id', true) "
            "OR current_setting('app.bypass_rls', true) = 'on'"
        )
        op.execute(
            f"CREATE POLICY tenant_isolation ON {name} "
            f"USING ({predicate}) WITH CHECK ({predicate})"
        )
    for table, index in (("sessions", "session"), ("tickets", "ticket")):
        op.execute(
            f"CREATE INDEX IF NOT EXISTS work_bridge_{index}_expiry "
            f"ON work_bridge_{table} (expires_at)"
        )


def downgrade():
    raise RuntimeError("Retain account identity records; application rollback is additive")
