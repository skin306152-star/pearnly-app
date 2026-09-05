"""Durable Cloud Tasks delivery receipts."""

from alembic import op

revision = "0122_cloud_task_deliveries"
down_revision = "0121_pos_product_name_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    from services.cloud_tasks.store import DDL, INTERNAL_ACL

    op.execute(DDL)
    op.execute(
        "CREATE TABLE IF NOT EXISTS cloud_task_locks ("
        "name TEXT PRIMARY KEY, owner UUID NOT NULL, lease_until TIMESTAMPTZ NOT NULL)"
    )
    op.execute("ALTER TABLE cloud_task_locks ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON cloud_task_locks FROM PUBLIC")
    op.execute("ALTER TABLE cloud_task_deliveries ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON cloud_task_deliveries FROM PUBLIC")
    op.execute(INTERNAL_ACL)
    op.execute(
        "CREATE INDEX IF NOT EXISTS cloud_task_pending "
        "ON cloud_task_deliveries(status, created_at)"
    )


def downgrade():
    raise RuntimeError("Delivery receipts require backup and drain before removal")
