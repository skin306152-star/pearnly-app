# -*- coding: utf-8 -*-
"""管家任务后台工人(B3 · 长任务异步化)。

范式镜像 services/ocr/jobs/worker.py 双模(embedded 默认 + standalone
`python -m services.steward.worker`),差别:不另建 job 表 —— steward_tasks 自己就是队列,
任务表就是进度表(steps jsonb 即步骤流水),再建一张 job 表会出现两处状态要对齐。
入队即 running(worker_id 空 = 还没被认领),认领走 FOR UPDATE SKIP LOCKED,租约 =
timeout_s + 宽限;失联(进程死/后台不在线)由 heal_stale 收成 failed,绝不永远转圈。

超时用 asyncio.wait_for 硬闸:工具线程杀不掉(Python 线程无强杀),但任务行如实落
failed + 原因,晚到的结果被 store.finish_task 的活态守卫拒收 —— 状态先诚实,资源随
进程回收。收尾时往会话追写一条管家消息(主动汇报),前端回页/轮询终态自动补回。
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import time
from typing import Optional

from services.agent.contracts import ToolResult
from services.steward import copy, store, tools
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"
_POLL_S = float(os.environ.get("STEWARD_WORKER_POLL_SEC", "1"))
_CONCURRENCY = int(os.environ.get("STEWARD_WORKER_CONCURRENCY", "2"))
_SWEEP_EVERY_S = 30.0

# 失联判定的宽限(秒):租约/入队时限都在 timeout_s 之上再放这么多,防边界抖动误杀。
STALE_GRACE_S = 60

ERR_TIMEOUT = "steward.timeout"
ERR_WORKER_LOST = "steward.worker_lost"
ERR_QUEUE_STALLED = "steward.queue_stalled"
ERR_CANCELLED = "steward.cancelled"
ERR_CRASHED = "steward.task_crashed"
ERR_CONTEXT_LOST = "steward.context_lost"


def heal_stale(cur, *, tenant_id: Optional[str] = None, task_id: Optional[str] = None) -> int:
    """失联任务收口(worker 周期扫 + 任务查询时就地扫,两条路共用):
    认领过但租约过期 → worker_lost;从没被认领且早超时限 → queue_stalled。
    落错误码 + 按任务语言的人话原因,没跑完的步骤如实标失败 —— 别让左窗永远转圈。"""
    rows = store.list_stale_tasks(cur, tenant_id=tenant_id, task_id=task_id, grace_s=STALE_GRACE_S)
    for row in rows:
        code = ERR_WORKER_LOST if row.get("worker_id") else ERR_QUEUE_STALLED
        reason = copy.fail_reason(code, _lang_of(row))
        store.finish_task(
            cur,
            tenant_id=str(row["tenant_id"]),
            task_id=str(row["id"]),
            status=store.TASK_FAILED,
            steps=store.fail_steps(row.get("steps") or [], reason),
            artifacts=row.get("artifacts") or [],
            error_code=code,
            error_message=reason,
        )
    return len(rows)


def _lang_of(row: dict) -> str:
    return (row.get("payload") or {}).get("lang") or copy.DEFAULT_LANG


def _build_context(payload: dict, tenant_id: str) -> Optional[ToolContext]:
    """重建执行身份:user 按 id 现查(封号/权限变更即时生效,不拿入队时的旧快照),
    租户对不上一律不跑 —— 异步执行没有请求上下文,身份闸在这里补,绝不越权。"""
    from services.auth.user_lookup import find_user_by_id

    user_id = str(payload.get("user_id") or "")
    user = find_user_by_id(user_id) if user_id else None
    if not user:
        return None
    if user.get("tenant_id") is not None and str(user["tenant_id"]) != str(tenant_id):
        return None
    allowed = payload.get("allowed_client_ids")
    return ToolContext(
        user=user,
        tenant_id=str(tenant_id),
        user_id=user_id,
        allowed_client_ids=None if allowed is None else frozenset(int(i) for i in allowed),
        lang=str(payload.get("lang") or copy.DEFAULT_LANG),
    )


async def _execute(row: dict) -> None:
    """跑一条已认领的任务:标步骤 running → 工具(带超时硬闸)→ 按真实结果收尾。"""
    task_id = str(row["id"])
    payload = row.get("payload") or {}
    tool = str(payload.get("tool") or "")
    lang = _lang_of(row)
    timeout_s = float(row.get("timeout_s") or store.default_timeout_s())

    ctx = await asyncio.to_thread(_build_context, payload, str(row["tenant_id"]))
    if ctx is None:
        await asyncio.to_thread(
            _finalize_failure, row, ERR_CONTEXT_LOST, copy.fail_reason(ERR_CONTEXT_LOST, lang)
        )
        return
    await asyncio.to_thread(_mark_tool_running, row, tool, lang)
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(tools.run, tool, ctx, payload.get("args") or {}),
            timeout=timeout_s,
        )
    except asyncio.TimeoutError:
        logger.warning("[steward-worker] task %s timeout after %.0fs", task_id, timeout_s)
        reason = copy.fail_reason(ERR_TIMEOUT, lang, seconds=max(1, round(timeout_s)))
        await asyncio.to_thread(_finalize_failure, row, ERR_TIMEOUT, reason)
        return
    except Exception:
        logger.exception("[steward-worker] task %s crashed", task_id)
        await asyncio.to_thread(
            _finalize_failure, row, ERR_CRASHED, copy.fail_reason(ERR_CRASHED, lang)
        )
        return
    await asyncio.to_thread(_finalize_result, row, tool, lang, result)


def _mark_tool_running(row: dict, tool: str, lang: str) -> None:
    from core import db

    steps = copy.build_steps(tool, lang, tool_state=store.STEP_RUNNING, summarize=store.STEP_QUEUED)
    with db.get_cursor(commit=True) as cur:
        store.update_steps(
            cur, tenant_id=str(row["tenant_id"]), task_id=str(row["id"]), steps=steps
        )


def _finalize_result(row: dict, tool: str, lang: str, result: ToolResult) -> None:
    """工具跑完:成功/失败都按真实结果落终态(文案装配与 M1 同步时代同一套 copy)。"""
    if result.ok:
        reply = copy.reply(tool, result.data or {}, lang)
        artifacts = copy.artifacts(tool, result.data or {}, lang)
        _finalize(
            row,
            status=store.TASK_DONE,
            reply=reply,
            steps=copy.build_steps(
                tool,
                lang,
                tool_state=store.STEP_DONE,
                detail=reply,
                links=copy.artifact_links(artifacts),
            ),
            artifacts=artifacts,
            trace=[{"tool": tool, "ok": True, "error": None}],
        )
        return
    reply = copy.error(result.error_code or "", result.data, lang)
    _finalize(
        row,
        status=store.TASK_FAILED,
        reply=reply,
        steps=copy.build_steps(tool, lang, tool_state=store.STEP_FAILED, detail=reply),
        artifacts=[],
        trace=[{"tool": tool, "ok": False, "error": result.error_code}],
        error_code=result.error_code or ERR_CRASHED,
        error_message=reply,
    )


def _finalize_failure(row: dict, code: str, reason: str) -> None:
    """任务级失败(超时/身份失效/意外崩):错误码 + 人话原因,步骤如实标失败。"""
    payload = row.get("payload") or {}
    tool = str(payload.get("tool") or "")
    lang = _lang_of(row)
    _finalize(
        row,
        status=store.TASK_FAILED,
        reply=reason,
        steps=copy.build_steps(tool, lang, tool_state=store.STEP_FAILED, detail=reason),
        artifacts=[],
        trace=[{"tool": tool, "ok": False, "error": code}],
        error_code=code,
        error_message=reason,
    )


def _finalize(
    row: dict,
    *,
    status: str,
    reply: str,
    steps: list,
    artifacts: list,
    trace: list,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """收尾 + 主动汇报一个事务:终态没落成(取消赛跑赢了)就不回话,结果整体丢弃。"""
    from core import db

    tenant_id = str(row["tenant_id"])
    task_id = str(row["id"])
    with db.get_cursor(commit=True) as cur:
        landed = store.finish_task(
            cur,
            tenant_id=tenant_id,
            task_id=task_id,
            status=status,
            steps=steps,
            artifacts=artifacts,
            error_code=error_code,
            error_message=error_message,
        )
        if landed and row.get("session_id"):
            store.add_message(
                cur,
                tenant_id=tenant_id,
                session_id=str(row["session_id"]),
                role=store.ROLE_STEWARD,
                text=reply,
                tool_trace=trace,
                task_id=task_id,
            )
            store.touch_session(cur, tenant_id=tenant_id, session_id=str(row["session_id"]))
    if not landed:
        logger.info("[steward-worker] task %s already terminal · late result dropped", task_id)


def _sweep_stale() -> int:
    from core import db

    with db.get_cursor(commit=True) as cur:
        return heal_stale(cur)


async def run_worker(stop_event: Optional[asyncio.Event] = None) -> None:
    """工人主循环 · embedded 与 standalone 共用(认领/执行/失联收口)。"""
    try:
        store.ensure_once()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[steward-worker] ensure_tables at start failed: {e}")
    logger.info(f"[steward-worker] start id={WORKER_ID} concurrency={_CONCURRENCY} poll={_POLL_S}s")
    running: set = set()
    last_sweep = 0.0
    while stop_event is None or not stop_event.is_set():
        try:
            now = time.time()
            if now - last_sweep > _SWEEP_EVERY_S:
                healed = await asyncio.to_thread(_sweep_stale)
                if healed:
                    logger.warning(f"[steward-worker] healed {healed} stale tasks")
                last_sweep = now

            if len(running) < _CONCURRENCY:
                row = await asyncio.to_thread(
                    store.claim_next_task, WORKER_ID, grace_s=STALE_GRACE_S
                )
                if row:
                    task = asyncio.create_task(_execute(row))
                    running.add(task)
                    task.add_done_callback(running.discard)
                    continue  # 还有空槽就接着认领,不空转
            await asyncio.sleep(_POLL_S)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"[steward-worker] loop error: {e}")
            await asyncio.sleep(_POLL_S)


# ── embedded 模式(默认 · web 进程内)──────────────────────────────
_embedded_task: Optional[asyncio.Task] = None
_embedded_stop: Optional[asyncio.Event] = None


def start_embedded() -> None:
    """app 启动时在当前事件循环起后台工人任务。幂等。

    STEWARD_ASYNC=0 是急停口:关掉后新任务没人认领,查询侧 heal_stale 会在超时限后
    把它们如实收 failed(queue_stalled)—— 急停也不假转圈。"""
    global _embedded_task, _embedded_stop
    if _embedded_task and not _embedded_task.done():
        return
    if os.environ.get("STEWARD_ASYNC", "1") != "1":
        logger.info("[steward-worker] STEWARD_ASYNC=0 · embedded worker not started")
        return
    _embedded_stop = asyncio.Event()
    _embedded_task = asyncio.create_task(run_worker(_embedded_stop))
    logger.info("[steward-worker] embedded worker started")


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
