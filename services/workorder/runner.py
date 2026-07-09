# -*- coding: utf-8 -*-
"""工单后台推进器(HTTP /run 的执行体)。

HTTP 不许长阻塞(真跑 ~100 张 OCR 要几分钟):路由把 advance() 交 FastAPI BackgroundTasks
后台跑,请求当即返回。选型理由(对比 recon_jobs 独立 worker):引擎已按步提交事务
(engine.cursor_factory),每步 step_done 落库即永久成立,进程被杀只丢当前步、下次 /run 从
下一未完成步续跑——不需要 recon worker 那套租约/回收来救「不可续跑的长任务」,也不必为工单
再拉一份 ML 栈。所以最简解 = 后台线程直接驱动引擎,每步独立事务提交(本模块)。

进程内 in-flight 去重防同一工单被并发重推;跨进程并发即便发生,也因 step_done 幂等键
(work_order_id, step)兜底不会重复落已完成步。台账事件 run_started / run_finished 供详情观测。
"""

from __future__ import annotations

import logging
import threading

from core import db
from services.workorder import engine, store, storage
from services.workorder.steps import real_handlers

logger = logging.getLogger(__name__)

RUN_STEP = "run"
EVT_RUN_STARTED = "run_started"
EVT_RUN_FINISHED = "run_finished"

_inflight_lock = threading.Lock()
_inflight: set = set()


def _intake_files(items: list[dict]) -> list[str]:
    """已登记来料的落盘路径 = intake 步的输入。补料端点先把文件登记成 items(走 intake 指纹),
    这里回喂其 file_ref,intake 步再幂等登记一遍(同字节不重复),无料则 intake 诚实 needs。"""
    return [it["file_ref"] for it in items if it.get("file_ref")]


def _try_claim(key: tuple) -> bool:
    with _inflight_lock:
        if key in _inflight:
            return False
        _inflight.add(key)
        return True


def _release(key: tuple) -> None:
    with _inflight_lock:
        _inflight.discard(key)


def advance(tenant_id: str, work_order_id: str) -> dict:
    """把某工单推进到底或首个卡点(缺料 needs / 挂起票 stuck)。每步独立事务提交。

    背景任务里跑,吞异常只记日志(已完成步已提交,下次 /run 续跑)——绝不让后台线程崩掉。
    返回结果字典仅供测试/日志断言。
    """
    key = (str(tenant_id), str(work_order_id))
    if not _try_claim(key):
        return {"skipped": "already_running"}
    try:
        with db.get_cursor(commit=True) as cur:
            items = store.list_items(cur, tenant_id=tenant_id, work_order_id=work_order_id)
            store.append_event(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                step=RUN_STEP,
                event_type=EVT_RUN_STARTED,
                actor="system:runner",
            )
        ctx = engine.StepContext(
            cur=None,
            tenant_id=str(tenant_id),
            work_order_id=str(work_order_id),
            data={
                "deliverables_dir": str(storage.deliverables_dir(tenant_id, work_order_id)),
                "intake_files": _intake_files(items),
            },
            cursor_factory=lambda: db.get_cursor(commit=True),
        )
        out = engine.run_work_order(ctx, handlers=real_handlers())
        result = {
            "completed": out.completed,
            "status": out.status,
            "stopped_at": out.stopped_at,
        }
        _finish(tenant_id, work_order_id, result)
        return result
    except Exception as e:  # noqa: BLE001 - 后台任务:吞异常记日志,已提交步保留,续跑可恢复
        logger.error(f"[workorder-runner] advance {work_order_id} failed: {e}")
        _finish(tenant_id, work_order_id, {"error": str(e)[:200]})
        return {"error": str(e)[:200]}
    finally:
        _release(key)


def _finish(tenant_id: str, work_order_id: str, result: dict) -> None:
    try:
        with db.get_cursor(commit=True) as cur:
            store.append_event(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                step=RUN_STEP,
                event_type=EVT_RUN_FINISHED,
                payload=result,
                actor="system:runner",
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[workorder-runner] finish-event {work_order_id} failed: {e}")
