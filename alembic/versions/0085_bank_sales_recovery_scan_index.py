# -*- coding: utf-8 -*-
"""银行倒推大脑收尾扫描部分索引(D6 · bank_sales_recovery)。

Revision ID: 0085_bank_sales_recovery_scan_index
Revises: 0084_dms_change_requests
Create Date: 2026-07-20

bank_sales_recovery._find_candidates 挂在 30s 循环上,每 tick 对全租户最大表
work_order_events 做外层 event_type='bank_sales_brain_failed' 谓词 + 相关子查询
max(bank_sales_brain_finished id) —— 无索引即全表 seq scan。partial 索引只覆盖两种大脑终态
事件、近零体积;event_type 前导 + (tenant_id, work_order_id, id) 让外层扫描与子查询 max 都走索引。

留档性质:prod alembic 指针停 0020,真正落索引靠 services/workorder/schema.py 的 RUNTIME_ALTERS
懒加载自愈(dual-run,与本迁移逐字对齐,tests/unit/test_workorder_schema.py 静态守)。
"""

from alembic import op

revision = "0085_bank_sales_recovery_scan_index"
down_revision = "0084_dms_change_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_wo_events_brain_terminal "
        "ON work_order_events (event_type, tenant_id, work_order_id, id) "
        "WHERE event_type IN ('bank_sales_brain_failed', 'bank_sales_brain_finished')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_wo_events_brain_terminal")
