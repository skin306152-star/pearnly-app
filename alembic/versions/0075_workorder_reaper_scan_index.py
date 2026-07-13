# -*- coding: utf-8 -*-
"""工单收尸扫描部分索引(MC2-A1 效率8)。

Revision ID: 0075_workorder_reaper_scan_index
Revises: 0074_line_intake_staging
Create Date: 2026-07-14

reaper 周期扫「status=running 且租约过期」的死单,全表里命中行极少——部分索引只覆盖
running 且持约的行,扫描不随工单总量线性变慢。

留档性质:prod alembic 指针停 0020,真正落索引靠 services/workorder/schema.py 的
RUNTIME_ALTERS 懒加载自愈(dual-run,与本迁移逐字对齐,tests/unit/test_workorder_schema.py
静态守)。
"""

from alembic import op

revision = "0075_workorder_reaper_scan_index"
down_revision = "0074_line_intake_staging"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_wo_dead_run_scan "
        "ON work_orders (run_lease_expires_at) "
        "WHERE status = 'running' AND run_lease_expires_at IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_wo_dead_run_scan")
