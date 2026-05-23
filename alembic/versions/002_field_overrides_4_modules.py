"""4 modules · add field_overrides JSONB · BUG-FIX-P1.1

REFACTOR-A2.2 + B3 第一次真 Alembic 迁移(借整改 Phase 1 P1.1 激活 · 铁律 #21 ✅)
docs/audits/2026-05-22-ocr-recon-audit.md §5 Phase 1 P1.1

统一『OCR vs 手改』追踪字段 · 4 模块的 task / row 表都加 field_overrides JSONB:
- M1 ocr_history             (一行一发票 · 用户改字段时记 {field: {ocr, user, ts}})
- M2 reconciliation_row      (一行一对账 row · 用户改字段时记同上)
- M3 gl_vat_tasks            (整任务 · 用户改 anchor / GL 字段时记同上)
- M4 bank_recon_v2_tasks     (整任务 · 跟现有 summary_json._anchor_overrides 双写 · P1.2 后切单源)

Schema:`field_overrides JSONB`(允许 NULL · 老 task 不动 · 新 task 写时填)
Schema 形态:`{field_name: {"ocr": <value>, "user": <value>, "ts": <iso8601>}, ...}`

不写 GIN index(JSONB 当前查询少 · 后续 P1.4 confidence 真查时再加 index 防过早优化)
不做数据迁移(field_overrides 默认 NULL · M4 现有 summary_json._anchor_overrides 暂不动 · P1.2 切单源时一并 backfill)

Revision ID: 002_field_overrides_4_modules
Revises: 001_baseline
Create Date: 2026-05-23
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002_field_overrides_4_modules"
down_revision: Union[str, Sequence[str], None] = "001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 4 模块 task / row 表 · 加 field_overrides JSONB
_TABLES = ["ocr_history", "reconciliation_row", "gl_vat_tasks", "bank_recon_v2_tasks"]


def upgrade() -> None:
    """加 field_overrides JSONB 列(允许 NULL · 老数据不动)"""
    for table in _TABLES:
        # IF NOT EXISTS 保 idempotent · 防 ensure_field_overrides_columns() 双跑撞车
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS field_overrides JSONB")


def downgrade() -> None:
    """删 field_overrides JSONB 列(回滚 · 老数据不动)"""
    for table in _TABLES:
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS field_overrides")
