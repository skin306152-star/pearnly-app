# -*- coding: utf-8 -*-
"""
对账任务后台工人(ADR-005 · BUG-FIX-RECON-ASYNC)。

双模:
  - embedded:web 进程启动时 start_embedded() 起一个后台 asyncio 任务轮询队列
            (单进程即可工作 · 不依赖独立服务 · 单 1.9G 内存机不双份加载 ML 栈)。
  - standalone:`python -m services.recon_jobs.worker`(独立 systemd · 冲量时用)。

认领走 store.claim_next(FOR UPDATE SKIP LOCKED)· 并发闸门 = 同时最多 CONCURRENCY 单。
长任务靠 progress_cb 写进度顺便续租;工人崩了 → 租约过期 → reclaim_stale 回收。
handler 签名:fn(params: dict, input_ref: list, progress_cb) -> (result_table, result_id)
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import socket
import time
import traceback
from typing import Callable, Dict, Optional

from . import store
from services.startup_lock import startup_ddl_lock

logger = logging.getLogger("recon_jobs.worker")

# job_type -> handler(params, input_ref, progress_cb) -> (result_table, result_id)
_HANDLERS: Dict[str, Callable] = {}

WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"
POLL_INTERVAL = float(os.environ.get("RECON_WORKER_POLL_SEC", "2"))
CONCURRENCY = int(os.environ.get("RECON_WORKER_CONCURRENCY", "2"))
LEASE_SEC = int(os.environ.get("RECON_WORKER_LEASE_SEC", "600"))
STAGE_DIR = os.environ.get("RECON_JOBS_STAGE_DIR", "/opt/mrpilot/var/recon_jobs")


def register_handler(job_type: str, fn: Callable) -> None:
    """注册某类对账的重活处理函数(run_* 模块在 import 时调用)。"""
    _HANDLERS[job_type] = fn
    logger.info(f"[recon-worker] handler registered: {job_type}")


def bootstrap_handlers() -> None:
    """导入 handler 模块触发注册(run_* 在 #14 落地)· 缺失不致命。"""
    try:
        import services.recon_jobs.handlers  # noqa: F401  (import 即注册)
    except Exception as e:
        logger.warning(f"[recon-worker] handlers not loaded yet: {e}")


def stage_dir_for(job_id: str) -> str:
    return os.path.join(STAGE_DIR, str(job_id))


def _cleanup_stage(job_id: str) -> None:
    d = stage_dir_for(job_id)
    try:
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[recon-worker] cleanup stage {job_id} failed: {e}")


def _run_one(job: Dict) -> None:
    """在线程里跑单个任务(同步)· 写结果/失败 · 清暂存文件。"""
    job_id = job.get("id")
    jtype = job.get("job_type")
    handler = _HANDLERS.get(jtype or "")
    if handler is None:
        logger.error(f"[recon-worker] no handler for job_type={jtype!r} (job {job_id})")
        store.fail(job_id, "no_handler")
        _cleanup_stage(job_id)
        return

    def progress_cb(p: dict) -> None:
        store.update_progress(job_id, p, worker_id=WORKER_ID, lease_seconds=LEASE_SEC)

    keep_stage = False  # S8 · needs_review 时留暂存(confirm 重对账复用 gl 文件)
    try:
        result = handler(job.get("params") or {}, job.get("input_ref") or [], progress_cb)
        # S8 · handler 返回 ("__needs_review__", payload) → 暂停等用户核对 OCR 行
        _sentinel = result[0] if isinstance(result, (tuple, list)) and len(result) == 2 else None
        if _sentinel == "__needs_review__":
            store.set_needs_review(job_id, result[1])
            keep_stage = True
            logger.info(f"[recon-worker] job {job_id} ({jtype}) -> needs_review(待用户核对)")
            return
        # BUG-FIX-RECON-GLCSV · 整侧解析失败不再静默 done:能弹列映射 → needs_mapping;否则 failed。
        if _sentinel == "__needs_mapping__":
            store.set_needs_mapping(job_id, result[1] or {})
            logger.info(f"[recon-worker] job {job_id} ({jtype}) -> needs_mapping(待用户确认列对应)")
            return
        if _sentinel == "__failed__":
            p = result[1] or {}
            store.set_failed(
                job_id,
                p.get("error_code") or "parse_failed",
                result_table=p.get("result_table"),
                result_id=p.get("result_id"),
            )
            logger.info(f"[recon-worker] job {job_id} ({jtype}) -> failed({p.get('error_code')})")
            return
        result_table: Optional[str] = None
        result_id = None
        if isinstance(result, (tuple, list)) and len(result) == 2:
            result_table, result_id = result
        store.finish(job_id, result_table or jtype, result_id)
        logger.info(f"[recon-worker] job {job_id} ({jtype}) done -> {result_table}:{result_id}")
    except Exception as e:  # noqa: BLE001
        logger.error(f"[recon-worker] job {job_id} ({jtype}) FAILED: {e}\n{traceback.format_exc()}")
        store.fail(job_id, "processing_error")
    finally:
        if not keep_stage:
            _cleanup_stage(job_id)


async def run_worker(stop_event: Optional[asyncio.Event] = None) -> None:
    """工人主循环 · embedded 与 standalone 共用。"""
    try:
        # workers=N 时每个进程的内嵌 worker 都会跑到这里 · 并发 CREATE/ALTER IF NOT EXISTS
        # 仍抢 recon_jobs 的 AccessExclusiveLock → 互相死锁(4-worker 首次建表实测回退过)。
        # 套启动 DDL 文件锁串行化(表多由 startup.py 先建好 · 此处幂等多为无操作)。
        with startup_ddl_lock():
            store.ensure_table()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[recon-worker] ensure_table at start failed: {e}")
    bootstrap_handlers()
    logger.info(
        f"[recon-worker] start id={WORKER_ID} concurrency={CONCURRENCY} poll={POLL_INTERVAL}s"
    )
    running: set = set()
    last_reclaim = 0.0
    while stop_event is None or not stop_event.is_set():
        try:
            now = time.time()
            if now - last_reclaim > max(LEASE_SEC / 2, 30):
                reclaimed = await asyncio.to_thread(store.reclaim_stale)
                if reclaimed:
                    logger.warning(f"[recon-worker] reclaimed stale jobs: {reclaimed}")
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
            logger.error(f"[recon-worker] loop error: {e}")
            await asyncio.sleep(POLL_INTERVAL)


# ── embedded 模式(默认 · web 进程内)──────────────────────────────
_embedded_task: Optional[asyncio.Task] = None
_embedded_stop: Optional[asyncio.Event] = None


def start_embedded() -> None:
    """从 app.py 启动事件里调 · 在当前事件循环起后台工人任务。幂等。"""
    global _embedded_task, _embedded_stop
    if _embedded_task and not _embedded_task.done():
        return
    if os.environ.get("RECON_ASYNC", "1") != "1":
        logger.info("[recon-worker] RECON_ASYNC!=1 · embedded worker not started")
        return
    _embedded_stop = asyncio.Event()
    _embedded_task = asyncio.create_task(run_worker(_embedded_stop))
    logger.info("[recon-worker] embedded worker started")


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
