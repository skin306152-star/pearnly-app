# -*- coding: utf-8 -*-
"""工单后台推进器(推进原语 request_run + 执行体 advance)。

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
import os
import threading
import uuid
from typing import Callable, Optional

from core import db
from services.workorder import engine, store, storage
from services.workorder.steps import real_handlers

logger = logging.getLogger(__name__)

RUN_STEP = "run"
EVT_RUN_REQUESTED = "run_requested"
EVT_RUN_STARTED = "run_started"
EVT_RUN_FINISHED = "run_finished"
# 后台 run 崩溃的诚实收尾事件(P-8):任何异常都落此(带 error 原因),与成功的 run_finished
# 分开,好让详情/接管方一眼看出「这次 run 死了」而非「跑完了」。run 级事件词汇单一事实源在此
# (与 routes 的 run_requested 一道构成 step="run" 的事件类型全集)。
EVT_RUN_FAILED = "run_failed"

_inflight_lock = threading.Lock()
_inflight: set = set()


def run_lease_ttl_seconds() -> int:
    """/run 租约有效期(秒)。默认 1800:远大于一次全量跑批(并发化后目标 <6 分钟),又能在
    进程猝死后自动过期让另一终端接管。env PEARNLY_WORKORDER_RUN_LEASE_TTL 覆写。"""
    try:
        return max(60, int(os.environ.get("PEARNLY_WORKORDER_RUN_LEASE_TTL", "1800")))
    except ValueError:
        return 1800


def request_run(
    tenant_id: str,
    work_order_id: str,
    *,
    actor: str,
    owner: Optional[str] = None,
    payload: Optional[dict] = None,
    lease: Optional[Callable] = None,
    background=None,
) -> Optional[str]:
    """统一推进原语(MC2-A1):抢租约 → 落 run_requested → 起后台 advance,单一事实源。

    四类入口(/run 路由、裁决/补料/补销项自驱、收尸续跑、LINE 答题回写)同走此路,不再各自
    拼「租约 + 事件 + 派发」三件套。lease 参数化获取策略:缺省 acquire_run_lease(常规抢约);
    收尸传 claim 重验闭包(死亡判据重验 + 认账事件与抢约同一事务);驳回重做传「抢约 + 翻状态」
    闭包(消灭 running-无租约窗口)。lease 返 False = 没抢到/不该跑 → 返 None,事务照常提交
    (闭包里已落的认账事件不回滚)。

    后台派发默认守护线程(不依赖 FastAPI,reaper 先例);background(BackgroundTasks)在场时
    用之——路由径「响应返回后才起跑」的既有优化,两者语义同源(advance 自带进程内去重 +
    run_failed 认账 + finally 释放租约)。
    """
    owner = owner or f"run:{uuid.uuid4().hex}"
    take = lease or store.acquire_run_lease
    store.ensure_runtime()  # 建租约列(独立事务)· 必须先于下面锁 work_orders 的 UPDATE
    with db.get_cursor(commit=True) as cur:
        if not take(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            owner=owner,
            ttl_seconds=run_lease_ttl_seconds(),
        ):
            return None
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=RUN_STEP,
            event_type=EVT_RUN_REQUESTED,
            payload=payload,
            actor=actor,
        )
    if background is not None:
        background.add_task(advance, tenant_id, work_order_id, owner)
    else:
        _spawn_advance(tenant_id, work_order_id, owner)
    return owner


def _spawn_advance(tenant_id: str, work_order_id: str, owner: str) -> None:
    """守护线程跑 advance(与 BackgroundTasks 等价:不阻塞调用方)。"""
    threading.Thread(
        target=advance,
        args=(tenant_id, work_order_id, owner),
        daemon=True,
        name=f"wo-run-{work_order_id[:8]}",
    ).start()


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


def is_inflight(tenant_id: str, work_order_id: str) -> bool:
    """本进程内该工单是否有 advance 在跑。收尸人的负向守卫:同进程可证活的 run(如超长跑批
    把租约耗过期)绝不误收;跨进程仍以租约过期为唯一死亡判据。"""
    with _inflight_lock:
        return (str(tenant_id), str(work_order_id)) in _inflight


def advance(tenant_id: str, work_order_id: str, lease_owner: str | None = None) -> dict:
    """把某工单推进到底或首个卡点(缺料 needs / 挂起票 stuck)。每步独立事务提交。

    背景任务里跑,吞异常只记日志(已完成步已提交,下次 /run 续跑)——绝不让后台线程崩掉。
    返回结果字典仅供测试/日志断言。lease_owner:路由抢到的 DB 租约持有者,收尾释放(供另一
    终端接管);None = 直调(CLI/测试)不涉租约。进程内 _inflight 是同进程快速去重的第二道闸。
    """
    key = (str(tenant_id), str(work_order_id))
    if not _try_claim(key):
        return {"skipped": "already_running"}
    try:
        store.ensure_runtime()  # 建租约/幂等键列(独立事务·先于任何锁工单表的 txn)
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
        data = {
            "deliverables_dir": str(storage.deliverables_dir(tenant_id, work_order_id)),
            "intake_files": _intake_files(items),
        }
        if lease_owner:
            # 逐件检查点心跳的料(classify._item_scope 顺带续约,MC2-A1 ④):只有持约的 run
            # 才续,直调(CLI/测试)不涉租约也就没有心跳。
            data["run_lease"] = {"owner": lease_owner, "ttl_seconds": run_lease_ttl_seconds()}
        ctx = engine.StepContext(
            cur=None,
            tenant_id=str(tenant_id),
            work_order_id=str(work_order_id),
            data=data,
            cursor_factory=lambda: db.get_cursor(commit=True),
        )
        out = engine.run_work_order(ctx, handlers=real_handlers())
        result = {
            "completed": out.completed,
            "status": out.status,
            "stopped_at": out.stopped_at,
        }
        _finish(tenant_id, work_order_id, EVT_RUN_FINISHED, result)
        return result
    except (
        Exception
    ) as e:  # noqa: BLE001 - 后台任务:异常落 run_failed 认账 + finally 释放租约,不静默死
        logger.exception(f"[workorder-runner] advance {work_order_id} failed")
        _finish(tenant_id, work_order_id, EVT_RUN_FAILED, {"error": str(e)[:200]})
        return {"error": str(e)[:200]}
    finally:
        # 无论成功/异常都释放租约(供另一终端接管)+ 解进程内去重锁。异常时 finish 已落
        # run_failed,这里的租约释放与 finish 各自独立 best-effort,任一失败不牵连另一个。
        _release(key)
        _release_lease(tenant_id, work_order_id, lease_owner)


def _release_lease(tenant_id: str, work_order_id: str, lease_owner: str | None) -> None:
    """收尾释放 DB 租约(仅路由抢租的调用有 owner)。best-effort:失败只记日志,租约会自然过期。"""
    if not lease_owner:
        return
    try:
        with db.get_cursor(commit=True) as cur:
            store.release_run_lease(
                cur, tenant_id=tenant_id, work_order_id=work_order_id, owner=lease_owner
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[workorder-runner] release-lease {work_order_id} failed: {e}")


def _finish(tenant_id: str, work_order_id: str, event_type: str, result: dict) -> None:
    """收尾台账:成功落 run_finished、异常落 run_failed(event_type 由调用方按结局定)。
    run_failed 同事务把状态落到 stuck(MC2-A1 ③):崩掉的 run 不许把 status 留在 running
    对 UI 谎称「AI 在做」——事件与状态列一起提交,词取 engine 权威常量不臆造。
    best-effort:落库失败只记日志,不牵连 finally 的租约释放(诚实收尾优先于事件必达)。"""
    try:
        with db.get_cursor(commit=True) as cur:
            store.append_event(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                step=RUN_STEP,
                event_type=event_type,
                payload=result,
                actor="system:runner",
            )
            if event_type == EVT_RUN_FAILED:
                store.set_status(
                    cur,
                    tenant_id=tenant_id,
                    work_order_id=work_order_id,
                    status=engine.STATUS_STUCK,
                )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[workorder-runner] finish-event {work_order_id} failed: {e}")
