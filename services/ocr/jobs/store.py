# -*- coding: utf-8 -*-
"""ocr_jobs 表 DB 访问层(缺口④ · 网页 OCR 上传异步)。

Postgres 当队列:认领走 SELECT ... FOR UPDATE SKIP LOCKED(多工人不抢同一单 · 不引 Redis)。
lease_until 租约:工人崩 / 部署重启 → 租约过期 · reclaim_stale() 回收(可重试回 queued · 否则 failed)。
镜像 services/recon_jobs/store.py;OCR 专属差异:
  · result   JSONB —— worker 成功后落"同形 recognize 响应",前端轮询拿到直接 ingestResult,零改渲染。
防重扣:max_attempts=1(claim 后 attempts=1,reclaim_stale 命中即置 failed 不回队)→ 任务至多执行一次,
扣费(在 run_recognition_core→persist 内)随之至多一次;再上传命中 file_hash 缓存不复扣。无需额外幂等闸。
"""

from __future__ import annotations

import json as _json
import logging
from typing import Any, Dict, List, Optional

from core.db import get_cursor, get_cursor_rls
from core.rls import apply_tenant_or_user_rls

logger = logging.getLogger("ocr_jobs")

VALID_JOB_TYPES = ("web_ocr",)

# 启动即建(Zihao 拍板:不手动跑 alembic)· 全 IF NOT EXISTS 幂等。
_DDL = [
    """
    CREATE TABLE IF NOT EXISTS ocr_jobs (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_type      TEXT NOT NULL DEFAULT 'web_ocr',
        user_id       UUID NOT NULL,
        tenant_id     UUID,
        workspace_client_id BIGINT,
        status        TEXT NOT NULL DEFAULT 'queued',
        progress      JSONB,
        params        JSONB,
        input_ref     JSONB,
        result        JSONB,
        history_ids   JSONB,
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
    "CREATE INDEX IF NOT EXISTS idx_ocr_jobs_status_created ON ocr_jobs (status, created_at)",
    "CREATE INDEX IF NOT EXISTS idx_ocr_jobs_user_created "
    "ON ocr_jobs (user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_ocr_jobs_tenant_created "
    "ON ocr_jobs (tenant_id, created_at DESC) WHERE tenant_id IS NOT NULL",
]


def ensure_table() -> bool:
    """启动时幂等建表(web lifespan + standalone 工人都调)· 失败不致命(返 False)。"""
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception as _ee:  # noqa: BLE001
        logger.warning(f"ensure_table: pgcrypto ext skip ({_ee})")
    try:
        with get_cursor(commit=True) as cur:
            for stmt in _DDL:
                cur.execute(stmt)
            # tenant_id + user_id:tenant 隔离 + 孤立用户(tenant NULL)经 user 兜底。
            # 用户面 enqueue/get 走带上下文 RLS 游标;worker 队列操作显式 bypass。
            apply_tenant_or_user_rls(cur, "ocr_jobs")
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"ensure_table failed [{type(e).__name__}]: {e}")
        return False


def _norm(row: Optional[dict]) -> Optional[Dict[str, Any]]:
    """RealDictCursor 行规范化:uuid/datetime → str · JSONB(progress/result/...)已是 dict/list。"""
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
    user_id: str,
    tenant_id: Optional[str],
    params: Optional[dict] = None,
    input_ref: Optional[list] = None,
    max_attempts: int = 1,
    job_id: Optional[str] = None,
    workspace_client_id: Optional[int] = None,
    job_type: str = "web_ocr",
) -> Optional[str]:
    """建一个 queued 任务 · 返回 job_id(uuid 字符串)。

    job_id 由 submit 接口预生成(用它命名暂存目录 STAGE_DIR/<job_id>/,worker 完成后按同 id 清理)。
    套账 workspace_client_id 随 job 行存(异步 worker 无 request,从行/params 取套账,绝不"看全租户")。
    """
    if job_type not in VALID_JOB_TYPES:
        raise ValueError(f"unknown job_type: {job_type!r}")
    p = _json.dumps(params or {}, ensure_ascii=False, default=str)
    ir = _json.dumps(input_ref or [], ensure_ascii=False, default=str)
    ma = int(max_attempts or 1)
    uid = str(user_id)
    tid = str(tenant_id) if tenant_id else None
    ws = int(workspace_client_id) if workspace_client_id is not None else None

    def _insert() -> Optional[str]:
        # 用户面 INSERT 走 RLS 上下文:WITH CHECK 要求 tenant 匹配 / 或 tenant 空时 user 匹配。
        with get_cursor_rls(tenant_id=tid, user_id=uid, workspace_client_id=ws, commit=True) as cur:
            if job_id:
                cur.execute(
                    """
                    INSERT INTO ocr_jobs (id, job_type, user_id, tenant_id, workspace_client_id,
                                          status, params, input_ref, max_attempts)
                    VALUES (%s::uuid, %s, %s::uuid, %s, %s, 'queued', %s::jsonb, %s::jsonb, %s)
                    RETURNING id
                    """,
                    (str(job_id), job_type, uid, tid, ws, p, ir, ma),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO ocr_jobs (job_type, user_id, tenant_id, workspace_client_id,
                                          status, params, input_ref, max_attempts)
                    VALUES (%s, %s::uuid, %s, %s, 'queued', %s::jsonb, %s::jsonb, %s)
                    RETURNING id
                    """,
                    (job_type, uid, tid, ws, p, ir, ma),
                )
            row = cur.fetchone()
            return str(row["id"]) if row else None

    try:
        return _insert()
    except Exception as e:
        # 自愈:表不存在(部署后首次/启动建表失败)→ 现场建表重试一次。
        msg = str(e).lower()
        if "ocr_jobs" in msg and (
            "does not exist" in msg or "undefined" in msg or "relation" in msg
        ):
            logger.warning(f"enqueue: ocr_jobs missing · ensure_table + retry ({e})")
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
        # bypass:后台 worker 跨租户认领队列(SKIP LOCKED),无 HTTP 单租户上下文。
        with get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                """
                UPDATE ocr_jobs
                SET status = 'running',
                    worker_id = %s,
                    started_at = COALESCE(started_at, now()),
                    lease_until = now() + (%s * interval '1 second'),
                    attempts = attempts + 1,
                    updated_at = now()
                WHERE id = (
                    SELECT id FROM ocr_jobs
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


def update_progress(job_id: str, progress: dict, lease_seconds: int = 600) -> bool:
    """写进度 + 续租(工人活着的心跳)。"""
    try:
        # bypass:worker 认领后按 job_id 写心跳/进度,跑在 worker 进程无请求上下文。
        with get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                """
                UPDATE ocr_jobs
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


def finish(
    job_id: str,
    result: Optional[dict] = None,
    history_ids: Optional[list] = None,
    progress: Optional[dict] = None,
) -> bool:
    """任务成功 · 落同形 recognize 响应(result)+ 持久 history_ids。"""
    try:
        # bypass:worker 完成回填(按 job_id),无请求上下文。
        with get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                """
                UPDATE ocr_jobs
                SET status = 'done',
                    result = COALESCE(%s::jsonb, result),
                    history_ids = COALESCE(%s::jsonb, history_ids),
                    progress = COALESCE(%s::jsonb, progress),
                    finished_at = now(),
                    lease_until = NULL,
                    updated_at = now()
                WHERE id = %s::uuid
                """,
                (
                    (
                        _json.dumps(result, ensure_ascii=False, default=str)
                        if result is not None
                        else None
                    ),
                    (
                        _json.dumps(history_ids, ensure_ascii=False, default=str)
                        if history_ids is not None
                        else None
                    ),
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
        # bypass:worker 失败重试/置失败(按 job_id),无请求上下文。
        with get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                """
                UPDATE ocr_jobs
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
            return bool(cur.fetchone())
    except Exception as e:
        logger.error(f"fail failed ({job_id}): {e}")
        return False


def set_failed(job_id: str, error_code: str) -> bool:
    """终态失败(不重试)· pipeline 硬错(损坏/空/非票)直接转人工,前端按失败展示明确原因。"""
    try:
        # bypass:worker 终态失败回填(按 job_id),无请求上下文。
        with get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                """
                UPDATE ocr_jobs
                SET status = 'failed',
                    error_code = %s,
                    finished_at = now(),
                    lease_until = NULL,
                    updated_at = now()
                WHERE id = %s::uuid
                """,
                (error_code, str(job_id)),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"set_failed failed ({job_id}): {e}")
        return False


def reclaim_stale() -> List[Dict[str, str]]:
    """回收租约过期的 running 任务(工人崩/部署重启)· 可重试回 queued · 否则 failed。"""
    try:
        # bypass:后台回收过期租约(扫全表跨租户),无请求上下文。
        with get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute("""
                UPDATE ocr_jobs
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
        # 用户面状态查询:RLS 上下文 + 应用层 WHERE 双道(防越权看别人任务)。
        with get_cursor_rls(tenant_id=tenant_id, user_id=user_id) as cur:
            where = ["id = %s::uuid"]
            args: List[Any] = [str(job_id)]
            if user_id is not None and tenant_id:
                where.append("(user_id = %s::uuid OR tenant_id = %s::uuid)")
                args += [str(user_id), str(tenant_id)]
            elif user_id is not None:
                where.append("user_id = %s::uuid")
                args.append(str(user_id))
            cur.execute(f"SELECT * FROM ocr_jobs WHERE {' AND '.join(where)}", tuple(args))
            return _norm(cur.fetchone())
    except Exception as e:
        logger.error(f"get failed ({job_id}): {e}")
        return None


def gc_old(done_days: int = 3, failed_days: int = 14) -> int:
    """清理老任务记录(暂存文件由工人单独清)· 返回删除行数。

    result 含抽取字段(PII)· OCR 结果已落 ocr_history(RLS),job.result 只为轮询取数,
    比 recon 更短保留(done 3 天 / failed 14 天)· 减少 PII 驻留。
    """
    try:
        # bypass:后台 GC 清理老任务(扫全表跨租户),无请求上下文。
        with get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                """
                DELETE FROM ocr_jobs
                WHERE (status = 'done'   AND finished_at < now() - (%s * interval '1 day'))
                   OR (status = 'failed' AND finished_at < now() - (%s * interval '1 day'))
                """,
                (int(done_days), int(failed_days)),
            )
            return cur.rowcount or 0
    except Exception as e:
        logger.warning(f"gc_old failed: {e}")
        return 0
