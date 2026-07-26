# -*- coding: utf-8 -*-
"""管家任务异步化(B3):steward_tasks 补队列/租约/超时/错误列。

Revision ID: 0089_steward_task_async
Revises: 0088_steward_tables
Create Date: 2026-07-27

steward_tasks 自己当队列(不另建 job 表):任务表就是进度表,再建一张 job 表会出现两处
状态要对齐。入队即 running(worker_id 空 = 还没被认领),认领 = 填 worker_id + 租约
(timeout_s + 宽限);失联收口(worker_lost / queue_stalled)与超时判定都靠这些列。
error_code / error_message:失败必须带机器码 + 人话原因(四态诚实,禁"failed 但说不清为何")。

留档性质:prod 不跑 alembic upgrade,真正落列靠 services/steward/store.ensure_tables()
首用幂等自愈(与本迁移逐字对齐)。
"""

from alembic import op

revision = "0089_steward_task_async"
down_revision = "0088_steward_tables"
branch_labels = None
depends_on = None

_COLUMNS = (
    "ADD COLUMN IF NOT EXISTS payload jsonb NOT NULL DEFAULT '{}'::jsonb",
    "ADD COLUMN IF NOT EXISTS timeout_s integer NOT NULL DEFAULT 300",
    "ADD COLUMN IF NOT EXISTS worker_id text",
    "ADD COLUMN IF NOT EXISTS lease_until timestamptz",
    "ADD COLUMN IF NOT EXISTS error_code text",
    "ADD COLUMN IF NOT EXISTS error_message text",
)


def upgrade() -> None:
    for clause in _COLUMNS:
        op.execute(f"ALTER TABLE steward_tasks {clause}")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_steward_tasks_active "
        "ON steward_tasks (created_at) WHERE status = 'running'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_steward_tasks_active")
    for column in (
        "payload",
        "timeout_s",
        "worker_id",
        "lease_until",
        "error_code",
        "error_message",
    ):
        op.execute(f"ALTER TABLE steward_tasks DROP COLUMN IF EXISTS {column}")
