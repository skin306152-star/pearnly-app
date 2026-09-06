"""Cowork stocktake snapshots and count history."""

from alembic import op
from core.rls import apply_tenant_workspace_rls
from services.stocktake.schema import DDL

revision = "0123_cowork_stocktake"
down_revision = "0122_cloud_task_deliveries"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(DDL)

    # Same tenant/workspace predicate as the serialized runtime schema gate.
    class Cursor:
        def execute(self, sql):
            op.execute(sql)

    apply_tenant_workspace_rls(
        Cursor(), "cowork_stocktakes", "cowork_stocktake_items", "cowork_stocktake_counts"
    )


def downgrade():
    raise RuntimeError(
        "Stocktake history is retained; restore from a reviewed backup to roll back schema"
    )
