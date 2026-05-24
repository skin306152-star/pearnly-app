"""recon_jobs · 对账异步任务队列/状态层 · BUG-FIX-RECON-ASYNC

ADR-005 对账中心异步任务化(大文件不超时 + 多用户可扩展)。
docs/refactor/adr-005-recon-async-jobs.md

新增 recon_jobs 表 = 三个对账(银行/收入/销项税)共用的"订单号 + 状态 + 进度"队列层。
结果仍写入现有结果表(bank_recon_v2_task / vat_recon_tasks / reconciliation_task)·
本表只用 result_table + result_id 指过去 → 历史/导出/KPI 全不改。

队列认领走 SELECT ... FOR UPDATE SKIP LOCKED(Postgres 当队列 · 不引 Redis)。
lease_until = 租约 · 工人崩了租约过期可被回收(防任务卡 running)。

Schema 形态:
  progress  JSONB  {stage, stage_done, stage_total, current_file, eta_sec, ...}
  params    JSONB  {gl_account, lang, anchor overrides, ...}
  input_ref JSONB  [{path, name, kind}]  暂存上传文件清单

Revision ID: 003_recon_jobs
Revises: 002_field_overrides_4_modules
Create Date: 2026-05-24
"""

from typing import Sequence, Union

from alembic import op

revision: str = "003_recon_jobs"
down_revision: Union[str, Sequence[str], None] = "002_field_overrides_4_modules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """建 recon_jobs 表 + 索引(IF NOT EXISTS 保幂等)"""
    op.execute("""
        CREATE TABLE IF NOT EXISTS recon_jobs (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_type      TEXT NOT NULL,                 -- 'bank' | 'glvat' | 'salesvat'
            user_id       UUID NOT NULL,
            tenant_id     UUID,
            status        TEXT NOT NULL DEFAULT 'queued',-- queued|running|done|failed|canceled
            progress      JSONB,
            params        JSONB,
            input_ref     JSONB,
            result_table  TEXT,
            result_id     TEXT,
            error_code    TEXT,
            attempts      INTEGER NOT NULL DEFAULT 0,
            max_attempts  INTEGER NOT NULL DEFAULT 1,
            worker_id     TEXT,
            lease_until   TIMESTAMPTZ,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            started_at    TIMESTAMPTZ,
            finished_at   TIMESTAMPTZ,
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """)
    # 工人认领扫描:按 status + 时间(FIFO)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_recon_jobs_status_created "
        "ON recon_jobs (status, created_at)"
    )
    # 用户/租户列自己的任务历史
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_recon_jobs_user_created "
        "ON recon_jobs (user_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_recon_jobs_tenant_created "
        "ON recon_jobs (tenant_id, created_at DESC) WHERE tenant_id IS NOT NULL"
    )


def downgrade() -> None:
    """删 recon_jobs 表(回滚)"""
    op.execute("DROP TABLE IF EXISTS recon_jobs")
