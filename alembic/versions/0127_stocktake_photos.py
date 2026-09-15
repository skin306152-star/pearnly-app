"""Stocktake photographic evidence."""

from alembic import op
from services.stocktake.photo_schema import apply

revision = "0127_stocktake_photos"
down_revision = "0126_dms_login_ticket_scope"
branch_labels = None
depends_on = None


def upgrade():
    class Cursor:
        def execute(self, sql):
            op.execute(sql)

    apply(Cursor())


def downgrade():
    raise RuntimeError("Stocktake evidence must be retained; rollback requires review")
