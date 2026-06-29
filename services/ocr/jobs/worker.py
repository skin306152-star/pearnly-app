# -*- coding: utf-8 -*-
"""网页 OCR 上传任务后台工人(缺口④)。

镜像 services/recon_jobs/worker.py 双模:
  - embedded:web 进程启动 start_embedded() 起后台 asyncio 任务轮询(单进程即可 · 不依赖独立服务)。
  - standalone:`python -m services.ocr.jobs.worker`(独立 systemd · 冲量时用)。

认领走 store.claim_next(FOR UPDATE SKIP LOCKED)· 并发闸门 = 同时最多 CONCURRENCY 单。
交互场景(用户在等结果)→ poll 默认 1s,比对账(2s)更勤。
handler 签名:fn(params, input_ref, progress_cb) -> {"result": <同形 recognize JSON>, "history_ids": [...]}
            终态失败返 ("__failed__", {"error_code": ...});可重试错直接 raise(回 queued / 终 failed)。
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
import shutil
import socket
import time
import traceback
from typing import Callable, Dict, Optional

from . import store
from services.startup_lock import startup_ddl_lock

logger = logging.getLogger("ocr_jobs.worker")

# job_type -> handler(params, input_ref, progress_cb) -> {"result":..., "history_ids":[...]}
_HANDLERS: Dict[str, Callable] = {}

WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"
POLL_INTERVAL = float(os.environ.get("OCR_WORKER_POLL_SEC", "1"))
CONCURRENCY = int(os.environ.get("OCR_WORKER_CONCURRENCY", "2"))
LEASE_SEC = int(os.environ.get("OCR_WORKER_LEASE_SEC", "600"))
STAGE_DIR = os.environ.get("OCR_JOBS_STAGE_DIR", "/opt/mrpilot/var/ocr_jobs")


def register_handler(job_type: str, fn: Callable) -> None:
    """注册某类 OCR 任务的处理函数(handler 模块 import 时调用)。"""
    _HANDLERS[job_type] = fn
    logger.info(f"[ocr-worker] handler registered: {job_type}")


def bootstrap_handlers() -> None:
    """导入 handler 模块触发注册 · 缺失不致命。"""
    try:
        handlers = importlib.import_module("services.ocr.jobs.handler")
        register = getattr(handlers, "_register", None)
        if callable(register):
            register()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[ocr-worker] handler not loaded yet: {e}")


def stage_dir_for(job_id: str) -> str:
    return os.path.join(STAGE_DIR, str(job_id))


def _cleanup_stage(job_id: str) -> None:
    d = stage_dir_for(job_id)
    try:
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[ocr-worker] cleanup stage {job_id} failed: {e}")


def _run_one(job: Dict) -> None:
    """在线程里跑单个任务(同步)· 写结果/失败 · 清暂存文件。"""
    job_id = job.get("id")
    jtype = job.get("job_type")
    handler = _HANDLERS.get(jtype or "")
    if handler is None:
        bootstrap_handlers()
        handler = _HANDLERS.get(jtype or "")
    if handler is None:
        known = ",".join(sorted(_HANDLERS)) or "-"
        logger.error(
            f"[ocr-worker] no handler for job_type={jtype!r} (job {job_id}); known={known}"
        )
        store.fail(job_id, "no_handler")
        _cleanup_stage(job_id)
        return

    def progress_cb(p: dict) -> None:
        store.update_progress(job_id, p, lease_seconds=LEASE_SEC)

    try:
        # 套账/归属随 job 行存(异步无 request)· 注入 params 供 handler 取,绝不"看全租户"。
        params = dict(job.get("params") or {})
        for key in ("job_id", "user_id", "tenant_id", "workspace_client_id"):
            row_key = "id" if key == "job_id" else key
            if params.get(key) is None and job.get(row_key) is not None:
                params[key] = job.get(row_key)

        result = handler(params, job.get("input_ref") or [], progress_cb)

        # 终态失败 sentinel:非票/损坏/空 → 转人工,前端按失败展示明确原因(绝不冒充完成)。
        if isinstance(result, (tuple, list)) and len(result) == 2 and result[0] == "__failed__":
            p = result[1] or {}
            store.set_failed(job_id, p.get("error_code") or "ocr_failed")
            logger.info(f"[ocr-worker] job {job_id} -> failed({p.get('error_code')})")
            return

        res = result or {}
        store.finish(
            job_id,
            result=res.get("result"),
            history_ids=res.get("history_ids"),
            progress={"stage": "done"},
        )
        n = len(res.get("history_ids") or [])
        logger.info(f"[ocr-worker] job {job_id} done -> {n} history rows")
    except Exception as e:  # noqa: BLE001
        logger.error(f"[ocr-worker] job {job_id} FAILED: {e}\n{traceback.format_exc()}")
        # 真错存进 error_code(前端/库可见)· 别吞成通用错误让人无从诊断。
        store.fail(job_id, (str(e).strip()[:200] or "processing_error"))
    finally:
        _cleanup_stage(job_id)


async def run_worker(stop_event: Optional[asyncio.Event] = None) -> None:
    """工人主循环 · embedded 与 standalone 共用。"""
    try:
        # 并发建表抢 AccessExclusiveLock 会互锁 → 套启动 DDL 文件锁串行化(多为幂等无操作)。
        with startup_ddl_lock():
            store.ensure_table()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[ocr-worker] ensure_table at start failed: {e}")
    bootstrap_handlers()
    logger.info(
        f"[ocr-worker] start id={WORKER_ID} concurrency={CONCURRENCY} poll={POLL_INTERVAL}s"
    )
    running: set = set()
    last_reclaim = 0.0
    while stop_event is None or not stop_event.is_set():
        try:
            now = time.time()
            if now - last_reclaim > max(LEASE_SEC / 2, 30):
                reclaimed = await asyncio.to_thread(store.reclaim_stale)
                if reclaimed:
                    logger.warning(f"[ocr-worker] reclaimed stale jobs: {reclaimed}")
                last_reclaim = now

            if len(running) < CONCURRENCY:
                job = await asyncio.to_thread(store.claim_next, WORKER_ID, LEASE_SEC)
                if job:
                    t = asyncio.create_task(asyncio.to_thread(_run_one, job))
                    running.add(t)
                    t.add_done_callback(running.discard)
                    continue  # 还有空槽就接着认领 · 不空转
            await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"[ocr-worker] loop error: {e}")
            await asyncio.sleep(POLL_INTERVAL)


# ── embedded 模式(默认 · web 进程内)──────────────────────────────
_embedded_task: Optional[asyncio.Task] = None
_embedded_stop: Optional[asyncio.Event] = None


def start_embedded() -> None:
    """从 app 启动事件里调 · 在当前事件循环起后台工人任务。幂等。

    闸 OCR_ASYNC_WEB(默认 off · 安全灰度):关时不起 worker,网页走同步老路。
    """
    global _embedded_task, _embedded_stop
    if _embedded_task and not _embedded_task.done():
        return
    if os.environ.get("OCR_ASYNC_WEB", "0") != "1":
        logger.info("[ocr-worker] OCR_ASYNC_WEB!=1 · embedded worker not started")
        return
    _embedded_stop = asyncio.Event()
    _embedded_task = asyncio.create_task(run_worker(_embedded_stop))
    logger.info("[ocr-worker] embedded worker started")


async def stop_embedded() -> None:
    global _embedded_task, _embedded_stop
    if _embedded_stop:
        _embedded_stop.set()
    if _embedded_task:
        try:
            await asyncio.wait_for(_embedded_task, timeout=5)
        except Exception:  # noqa: BLE001
            _embedded_task.cancel()


# ── standalone 模式 ───────────────────────────────────────────────
def _main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    _main()
