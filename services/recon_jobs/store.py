# -*- coding: utf-8 -*-
"""
recon_jobs 表 DB 访问层(ADR-005 · BUG-FIX-RECON-ASYNC)。

Postgres 当队列:认领走 SELECT ... FOR UPDATE SKIP LOCKED(多工人不抢同一单 · 不引 Redis)。
lease_until 租约:工人崩了 / 部署重启 → 租约过期 · reclaim_stale() 回收(能重试回 queued · 否则 failed)。

新业务 DB 函数按铁律 #21/#23 放 services/ · 不进 db.py。复用 db.get_cursor()。
"""

from __future__ import annotations

import json as _json
import logging
from typing import Any, Dict, List, Optional

from db import get_cursor

logger = logging.getLogger("recon_jobs")

VALID_JOB_TYPES = ("bank", "glvat", "salesvat")

# Alembic 003 是 schema 单一权威源;下面 DDL 与之逐字一致,只为『工人/web 启动时自动建表』
# (Zihao 2026-05-24 拍板:不手动跑 alembic · 启动即建)· 全 IF NOT EXISTS 幂等。
_DDL = [
    """
    CREATE TABLE IF NOT EXISTS recon_jobs (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_type      TEXT NOT NULL,
        user_id       UUID NOT NULL,
        tenant_id     UUID,
        status        TEXT NOT NULL DEFAULT 'queued',
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
    """,
    "CREATE INDEX IF NOT EXISTS idx_recon_jobs_status_created ON recon_jobs (status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_recon_jobs_user_created "
    "ON recon_jobs (user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_recon_jobs_tenant_created "
    "ON recon_jobs (tenant_id, created_at DESC) WHERE tenant_id IS NOT NULL",
]


def ensure_table() -> bool:
    """启动时幂等建表(web lifespan + standalone 工人都调)· 失败不致命(返 False)。

    pgcrypto:Supabase/PG13+ 的 gen_random_uuid 在 pgcrypto · 先确保扩展在(submit 走显式
    job_id 不依赖它 · 但不传 job_id 的入队走 DEFAULT 会用到)· CREATE EXTENSION 受限则忽略。
    """
    # pgcrypto 单独一个事务 · 失败不能污染建表事务(PG 里一条语句报错会让整个事务作废)
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception as _ee:  # noqa: BLE001
        logger.warning(f"ensure_table: pgcrypto ext skip ({_ee})")
    try:
        with get_cursor(commit=True) as cur:
            for stmt in _DDL:
                cur.execute(stmt)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"ensure_table failed [{type(e).__name__}]: {e}")
        return False


def _norm(row: Optional[dict]) -> Optional[Dict[str, Any]]:
    """RealDictCursor 行规范化:uuid/datetime → str · JSONB 已是 dict/list。"""
    if not row:
        return None
    out: Dict[str, Any] = dict(row)
    for k in ("id", "user_id", "tenant_id"):
        if out.get(k) is not None:
            out[k] = str(out[k])
    for k in ("created_at", "started_at", "finished_at", "updated_at", "lease_until"):
        v = out.get(k)
        if v is not None and hasattr(v, "isoformat"):
            out[k] = v.isoformat()
    return out


def enqueue(
    job_type: str,
    user_id: str,
    tenant_id: Optional[str],
    params: Optional[dict] = None,
    input_ref: Optional[list] = None,
    max_attempts: int = 1,
    job_id: Optional[str] = None,
) -> Optional[str]:
    """建一个 queued 任务 · 返回 job_id(uuid 字符串)。

    job_id 可由调用方预生成(submit 接口先用它命名暂存目录 STAGE_DIR/<job_id>/ ·
    工人完成后按同一 id 清理)· 不传则 DB gen_random_uuid()。
    """
    if job_type not in VALID_JOB_TYPES:
        raise ValueError(f"unknown job_type: {job_type!r}")
    p = _json.dumps(params or {}, ensure_ascii=False, default=str)
    ir = _json.dumps(input_ref or [], ensure_ascii=False, default=str)
    ma = int(max_attempts or 1)
    uid = str(user_id)
    tid = str(tenant_id) if tenant_id else None

    def _insert() -> Optional[str]:
        with get_cursor(commit=True) as cur:
            if job_id:
                cur.execute(
                    """
                    INSERT INTO recon_jobs (id, job_type, user_id, tenant_id, status,
                                            progress, params, input_ref, max_attempts)
                    VALUES (%s::uuid, %s, %s::uuid, %s, 'queued',
                            %s::jsonb, %s::jsonb, %s::jsonb, %s)
                    RETURNING id
                    """,
                    (str(job_id), job_type, uid, tid, p, ir, ma),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO recon_jobs (job_type, user_id, tenant_id, status,
                                            progress, params, input_ref, max_attempts)
                    VALUES (%s, %s::uuid, %s, 'queued', %s::jsonb, %s::jsonb, %s::jsonb, %s)
                    RETURNING id
                    """,
                    (job_type, uid, tid, p, ir, ma),
                )
            row = cur.fetchone()
            return str(row["id"]) if row else None

    try:
        return _insert()
    except Exception as e:
        # 自愈:表不存在(部署后首次/启动建表失败)→ 现场建表重试一次。
        msg = str(e).lower()
        if "recon_jobs" in msg and ("does not exist" in msg or "undefined" in msg or "relation" in msg):
            logger.warning(f"enqueue: recon_jobs missing · ensure_table + retry ({e})")
            if ensure_table():
                try:
                    return _insert()
                except Exception as e2:
                    logger.error(f"enqueue retry after ensure_table failed: {e2}")
                    return None
        logger.error(f"enqueue failed: {e}")
        return None


def claim_next(worker_id: str, lease_seconds: int = 600) -> Optional[Dict[str, Any]]:
    """原子认领下一个 queued 任务(FOR UPDATE SKIP LOCKED)· 置 running + 续租 · 返回任务行。

    无可认领 → None。多工人并发安全:SKIP LOCKED 保证不会两个工人抢到同一单。
    """
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE recon_jobs
                SET status = 'running',
                    worker_id = %s,
                    started_at = COALESCE(started_at, now()),
                    lease_until = now() + (%s * interval '1 second'),
                    attempts = attempts + 1,
                    updated_at = now()
                WHERE id = (
                    SELECT id FROM recon_jobs
                    WHERE status = 'queued'
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING *
                """,
                (str(worker_id), int(lease_seconds)),
            )
            return _norm(cur.fetchone())
    except Exception as e:
        logger.error(f"claim_next failed: {e}")
        return None


def update_progress(
    job_id: str, progress: dict, worker_id: Optional[str] = None, lease_seconds: int = 600
) -> bool:
    """写进度 + 续租(工人活着的心跳)。"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE recon_jobs
                SET progress = %s::jsonb,
                    lease_until = now() + (%s * interval '1 second'),
                    updated_at = now()
                WHERE id = %s::uuid AND status = 'running'
                """,
                (
                    _json.dumps(progress or {}, ensure_ascii=False, default=str),
                    int(lease_seconds),
                    str(job_id),
                ),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.warning(f"update_progress failed ({job_id}): {e}")
        return False


def finish(job_id: str, result_table: str, result_id: Any, progress: Optional[dict] = None) -> bool:
    """任务成功 · 回填结果指针(指向现有结果表)。"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE recon_jobs
                SET status = 'done',
                    result_table = %s,
                    result_id = %s,
                    progress = COALESCE(%s::jsonb, progress),
                    finished_at = now(),
                    lease_until = NULL,
                    updated_at = now()
                WHERE id = %s::uuid
                """,
                (
                    result_table,
                    str(result_id) if result_id is not None else None,
                    _json.dumps(progress, ensure_ascii=False, default=str) if progress else None,
                    str(job_id),
                ),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"finish failed ({job_id}): {e}")
        return False


def fail(job_id: str, error_code: str) -> bool:
    """任务失败 · 还有重试次数则回 queued · 否则 failed。"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                UPDATE recon_jobs
                SET status = CASE WHEN attempts < max_attempts THEN 'queued' ELSE 'failed' END,
                    error_code = %s,
                    worker_id = NULL,
                    lease_until = NULL,
                    finished_at = CASE WHEN attempts < max_attempts THEN finished_at ELSE now() END,
                    updated_at = now()
                WHERE id = %s::uuid
                RETURNING status
                """,
                (error_code, str(job_id)),
            )
            row = cur.fetchone()
            return bool(row)
    except Exception as e:
        logger.error(f"fail failed ({job_id}): {e}")
        return False


def reclaim_stale() -> List[Dict[str, str]]:
    """回收租约过期的 running 任务(工人崩/部署重启)· 能重试回 queued · 否则 failed。

    工人循环里定期调。返回被回收的 [{id, status}]。
    """
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE recon_jobs
                SET status = CASE WHEN attempts < max_attempts THEN 'queued' ELSE 'failed' END,
                    error_code = CASE WHEN attempts < max_attempts THEN error_code ELSE 'worker_lost' END,
                    worker_id = NULL,
                    lease_until = NULL,
                    finished_at = CASE WHEN attempts < max_attempts THEN finished_at ELSE now() END,
                    updated_at = now()
                WHERE status = 'running' AND lease_until IS NOT NULL AND lease_until < now()
                RETURNING id, status
                """)
            return [{"id": str(r["id"]), "status": r["status"]} for r in (cur.fetchall() or [])]
    except Exception as e:
        logger.warning(f"reclaim_stale failed: {e}")
        return []


def get(
    job_id: str, user_id: Optional[str] = None, tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """取单个任务(状态接口用)· 传 user_id/tenant_id 则做归属校验(防越权看别人任务)。"""
    try:
        with get_cursor() as cur:
            where = ["id = %s::uuid"]
            args: List[Any] = [str(job_id)]
            if user_id is not None and tenant_id:
                where.append("(user_id = %s::uuid OR tenant_id = %s::uuid)")
                args += [str(user_id), str(tenant_id)]
            elif user_id is not None:
                where.append("user_id = %s::uuid")
                args.append(str(user_id))
            cur.execute(f"SELECT * FROM recon_jobs WHERE {' AND '.join(where)}", tuple(args))
            return _norm(cur.fetchone())
    except Exception as e:
        logger.error(f"get failed ({job_id}): {e}")
        return None


def gc_old(done_days: int = 7, failed_days: int = 30) -> int:
    """清理老任务记录(暂存文件由工人单独清)· 返回删除行数。"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                """
                DELETE FROM recon_jobs
                WHERE (status = 'done'   AND finished_at < now() - (%s * interval '1 day'))
                   OR (status = 'failed' AND finished_at < now() - (%s * interval '1 day'))
                """,
                (int(done_days), int(failed_days)),
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.warning(f"gc_old failed: {e}")
        return 0
