"""purchase_docs 加 image_sha256(LINE 图片票早期去重短路 · P1G-Perf)。

Revision ID: 0043_purchase_image_sha256
Revises: 0042_purchase_payment_method
Create Date: 2026-06-18

同一张照片再次发来时,据 image_sha256(图片字节指纹·下载即可算)找到上次建的单据,直接重发
当前状态卡,跳过 Vision/Gemini/分类(治「重复票仍跑满 60s」)。dedupe_key 是内容指纹(需先
OCR 才能算),救不了时间;image_sha256 在 OCR 前即可短路。建部分索引(仅非空行)。Dual-run:
prod 无 alembic 钩子,走 services/purchase/schema.ensure_purchase_schema() 的幂等 ALTER;本文件留档。
"""

from alembic import op

revision = "0043_purchase_image_sha256"
down_revision = "0042_purchase_payment_method"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE purchase_docs ADD COLUMN IF NOT EXISTS image_sha256 text")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_purchase_docs_image_sha "
        "ON purchase_docs (tenant_id, workspace_client_id, image_sha256) "
        "WHERE image_sha256 IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_purchase_docs_image_sha")
    op.execute("ALTER TABLE purchase_docs DROP COLUMN IF EXISTS image_sha256")
