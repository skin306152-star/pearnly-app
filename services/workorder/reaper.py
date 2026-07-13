# -*- coding: utf-8 -*-
"""部署中断工单收尸(MC2-0)。

MC1-a 治进程内崩溃(异常 → run_failed 认账 + finally 释放租约),治不了进程被杀
(部署重启的 SIGKILL 来不及 finally):工单停在 status=running、租约悬着,UI 数小时
谎称「AI 在做」。本模块补这条腿——死亡判据 =「活 run 必持未过期租约」不变式的完整
表达(store._DEAD_RUN_PREDICATE 单一事实源;禁其它猜测性判据):status=running 且
①租约已过期(被杀实锤)或 ②租约 NULL 且 updated_at 老于 TTL 宽限(翻了 running 却
没拿到租约的孤儿,MC2-A1 F3)。逐单:落 run_failed(reason=interrupted)认账 →
自动重新入跑(引擎按事件流检查点续跑,已完成件不重烧 OCR)。

两处挂钩同一实现,都在 services/background_loops.py:服务启动跑一次(erp_retry_loop
开场)+ 周期巡检(run_recovery_tick,LINE 恢复/主动触达同挂点)。

防毒丸熔断:无人值守自动重跑限 AUTO_RESUME_LIMIT 次,从事件流数收尸人落的
run_requested 现算(不加列);人工 run_requested 重置预算——熔断防的是 crash-loop
烧 OCR 钱,人已介入即重新放行。超限落 run_failed + 工单置 stuck(现有状态词),
不再自动爬,可手动 /run。
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from core import db
from services.workorder import engine, runner, store

logger = logging.getLogger(__name__)

ACTOR_REAPER = "system:reaper"
REASON_INTERRUPTED = "interrupted"
AUTO_RESUME_LIMIT = 3
# 超限停机的人话原因(进 step_stuck 事件 reasons,详情读侧 _halt_info 原样展示)。
REASON_EXHAUSTED = "run_interrupted_auto_resume_exhausted"


async def run_tick() -> None:
    """挂点入口(启动一次 + background_loops.run_recovery_tick 周期巡检,两处同此)。
    扫描/收尸只是几条短 SQL,真正的续跑交守护线程,不占挂点节拍;自吞异常,挂点
    (startup/巡检 loop)不因收尸失败而死。"""
    try:
        await asyncio.to_thread(reap_dead_runs)
    except Exception as e:  # noqa: BLE001 - 挂点安全:失败记日志,下一轮巡检再试
        logger.warning(f"[workorder-reaper] tick failed: {e}")


def reap_dead_runs(limit: int = 20) -> dict:
    """收尸一轮:找死单 → 逐单收尸(每单独立事务,一单失败不连坐)。返回统计供日志/测试。"""
    store.ensure_runtime()  # 建租约列(独立事务)· 先于任何锁工单表的事务
    with db.get_cursor() as cur:
        dead = store.list_dead_runs(
            cur,
            status=engine.STATUS_RUNNING,
            orphan_grace_seconds=runner.run_lease_ttl_seconds(),
            limit=limit,
        )
    stats = {"reaped": 0, "resumed": 0, "halted": 0}
    for row in dead:
        try:
            _reap_one(str(row["tenant_id"]), str(row["id"]), stats)
        except Exception:  # noqa: BLE001 - 一单失败不连坐下一单
            logger.exception(f"[workorder-reaper] reap {row.get('id')} failed")
    if stats["reaped"]:
        logger.info(f"[workorder-reaper] {stats}")
    return stats


def _reap_one(tenant_id: str, work_order_id: str, stats: dict) -> None:
    """收一张死单:抢占 → run_failed 认账 → 续跑或熔断。

    走 runner.request_run(与 /run 路由/自驱/LINE 回写同一条推进路径),租约获取策略换成
    收尸闭包:claim_dead_run 单句条件 UPDATE 重验死亡判据(多 worker 并发收尸恰一个赢),
    认账事件、熔断裁决与抢占同一事务;熔断时闭包返 False(事务照常提交认账),不续跑。
    赢家的租约由 request_run 交给后台 advance,收尾 finally 释放。"""
    if runner.is_inflight(tenant_id, work_order_id):
        return  # 本进程可证活(超长跑批耗过期租约),不误收
    payload: dict = {}

    def claim_and_acknowledge(cur, *, tenant_id, work_order_id, owner, ttl_seconds) -> bool:
        if not store.claim_dead_run(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            owner=owner,
            ttl_seconds=ttl_seconds,
            status=engine.STATUS_RUNNING,
            orphan_grace_seconds=ttl_seconds,
        ):
            return False
        actors = store.list_event_actors(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=runner.RUN_STEP,
            event_type=runner.EVT_RUN_REQUESTED,
        )
        resumes = auto_resume_count(actors)
        exhausted = resumes >= AUTO_RESUME_LIMIT
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=runner.RUN_STEP,
            event_type=runner.EVT_RUN_FAILED,
            payload={
                "error": "process killed mid-run (lease expired)",
                "reason": REASON_INTERRUPTED,
                "auto_resume_used": resumes,
                "auto_resume_limit": AUTO_RESUME_LIMIT,
                "auto_resume_exhausted": exhausted,
            },
            actor=ACTOR_REAPER,
        )
        stats["reaped"] += 1
        if exhausted:
            _halt_exhausted(cur, tenant_id, work_order_id, owner)
            stats["halted"] += 1
            return False
        payload["auto_resume"] = resumes + 1
        return True

    scheduled = runner.request_run(
        tenant_id,
        work_order_id,
        actor=ACTOR_REAPER,
        owner=f"reaper:{uuid.uuid4().hex}",
        payload=payload,
        lease=claim_and_acknowledge,
    )
    if scheduled:
        stats["resumed"] += 1


def _halt_exhausted(cur, tenant_id: str, work_order_id: str, owner: str) -> None:
    """熔断停机:step_stuck(带人话原因)+ 工单置 stuck + 释放租约。全用现有词汇
    (engine.EVT_STUCK / STATUS_STUCK),详情读侧 _halt_info 直接如实显示,不碰前端。
    status 离开 running 后死亡判据不再命中,收尸人不会反复重收这张单。"""
    store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=runner.RUN_STEP,
        event_type=engine.EVT_STUCK,
        payload={"reasons": [f"{REASON_EXHAUSTED}:{AUTO_RESUME_LIMIT}"]},
        actor=ACTOR_REAPER,
    )
    store.set_status(
        cur, tenant_id=tenant_id, work_order_id=work_order_id, status=engine.STATUS_STUCK
    )
    store.release_run_lease(cur, tenant_id=tenant_id, work_order_id=work_order_id, owner=owner)


def auto_resume_count(request_actors: list[str]) -> int:
    """已连续用掉的自动重跑次数,从事件流现算(不加列):数最后一条人为 run_requested 之后
    收尸人落的 run_requested(入参 = run_requested 事件的 actor 序列,按发生序,取自
    store.list_event_actors 窄读)。人工重跑重置计数——熔断管无人值守 crash-loop,人已介入
    即重新给满预算。"""
    n = 0
    for actor in request_actors:
        n = n + 1 if actor == ACTOR_REAPER else 0
    return n
