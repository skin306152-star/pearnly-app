"""工单运行时加固:running 租约(防重入)+ 事件幂等键(C-1)。

Revision ID: 0066_workorder_runtime_hardening
Revises: 0065_users_username_lower_uniq, 0059_workorder_core
Create Date: 2026-07-10

同时收编 0058 之后分叉的两条链(0059_workorder_core 与 0065 主链)成单 head。

留档性质:prod alembic 指针停 0020,本迁移不自动上生产;真正落列/落索引靠
services/workorder/schema.py::ensure_runtime_hardening() 懒加载自愈(同 0060_ai_usage
的 dual-run 范式)。两份 DDL(本迁移 + schema.RUNTIME_ALTERS)保持逐字对齐,幂等
(ADD COLUMN / CREATE INDEX 均 IF NOT EXISTS),重复升级空操作。

两处加固:
  - work_orders.run_lease_owner / run_lease_expires_at:/run 推进的持有者 + 过期时间。
    双终端并发 /run 靠单句条件 UPDATE 抢租约,抢不到者 409;过期租约可被接管。
  - work_order_events.dedupe_key + 部分唯一索引:带 dedupe_key 的事件重放不重记
    (append_event ON CONFLICT DO NOTHING);dedupe_key 为空的事件(step_started 等)
    照旧可重复落,不受约束。

(原始文件名保留走 storage 落盘名内嵌 `{uuid}__{原名}`,不占 schema 列,见 storage.py。)
"""

from alembic import op

revision = "0066_workorder_runtime_hardening"
down_revision = ("0065_users_username_lower_uniq", "0059_workorder_core")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE work_orders ADD COLUMN IF NOT EXISTS run_lease_owner text")
    op.execute("ALTER TABLE work_orders ADD COLUMN IF NOT EXISTS run_lease_expires_at timestamptz")
    op.execute("ALTER TABLE work_order_events ADD COLUMN IF NOT EXISTS dedupe_key text")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_wo_events_dedupe "
        "ON work_order_events (tenant_id, work_order_id, step, event_type, dedupe_key) "
        "WHERE dedupe_key IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_wo_events_dedupe")
    op.execute("ALTER TABLE work_order_events DROP COLUMN IF EXISTS dedupe_key")
    op.execute("ALTER TABLE work_orders DROP COLUMN IF EXISTS run_lease_expires_at")
    op.execute("ALTER TABLE work_orders DROP COLUMN IF EXISTS run_lease_owner")
