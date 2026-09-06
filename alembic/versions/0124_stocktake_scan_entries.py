"""Scan-first stocktake entries and immutable operation audit."""

from alembic import op
from services.stocktake.entry_schema import apply

revision = "0124_stocktake_scan_entries"
down_revision = "0123_cowork_stocktake"
branch_labels = None
depends_on = None


def upgrade():
    class Cursor:
        def execute(self, sql):
            op.execute(sql)

    apply(Cursor())


def downgrade():
    raise RuntimeError("Stocktake entries and audit must be retained; schema rollback needs review")
