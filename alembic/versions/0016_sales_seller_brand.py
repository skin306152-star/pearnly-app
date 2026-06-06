"""Seller brand + template columns (docs/16 §L4 / H).

Revision ID: 0016_sales_seller_brand
Revises: 0015_sales_promptpay_wht
Create Date: 2026-06-06

Accounting firms keep books for many companies, each wanting its own invoice branding. The
template strategy = curated presets + per-account brand (not upload-and-learn): each account
(workspace_clients) stores a `template_id` plus brand assets (color / logo / seal / signature /
footer). The renderer reads these and applies the chosen layout + accent. Brand is frozen into
the document's parties_snapshot at issue, so the buyer's copy and the archival hash stay stable.

All columns nullable -> backward compatible (renderer falls back to the classic preset). Isolation
stays app-layer (get_cursor_rls + DAL WHERE tenant_id); names written literally.
"""

from alembic import op

revision = "0016_sales_seller_brand"
down_revision = "0015_sales_promptpay_wht"
branch_labels = None
depends_on = None

_COLUMNS = ("template_id", "brand_color", "logo_url", "seal_url", "signature_url", "footer_text")


def upgrade() -> None:
    for col in _COLUMNS:
        op.execute(f"ALTER TABLE workspace_clients ADD COLUMN IF NOT EXISTS {col} text")


def downgrade() -> None:
    for col in _COLUMNS:
        op.execute(f"ALTER TABLE workspace_clients DROP COLUMN IF EXISTS {col}")
