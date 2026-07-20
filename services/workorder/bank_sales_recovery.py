# -*- coding: utf-8 -*-
"""银行倒推大脑失败批自动收尾(D6 · 挂 background_loops.run_recovery_tick,禁新 cron)。

熔断/整轮失败的大脑分类会落 bank_sales_brain_failed 事件、入账行留 pending 却无人再点火——
本模块补自愈腿:周期扫「最近一条大脑终态是 failed、仍有 pending 行、自动重试预算未耗尽」的
工单,逐单起后台 run_async(经 begin_run 抢跨进程租约,重复扫描/多 worker 天然不双跑)。
逐单不连坐;重试也熔断(预算 AUTO_RETRY_LIMIT 耗尽)则停手等人——人工 /run 落 manual 终态
不计预算,人一介入即另算。

跨租户系统扫描(后台任务无单租户上下文,隔离靠逐单显式 tenant_id),与 reaper/auto_open 同口径。
"""

from __future__ import annotations

import asyncio
import logging
import threading

from core import db, feature_flags
from services.workorder import engine, store
from services.workorder.steps import bank_sales_brain as brain
from services.workorder.steps import bank_sales_suggest as suggest

logger = logging.getLogger(__name__)

AUTO_RETRY_LIMIT = 3
_SCAN_LIMIT = 20


async def run_tick() -> int:
    """挂点入口:扫描丢线程池(同步 DB 不阻塞事件循环);自吞异常,失败下一轮巡检再试。"""
    try:
        return await asyncio.to_thread(scan_and_resume)
    except Exception as e:  # noqa: BLE001 - 挂点安全
        logger.warning(f"[bank-sales-recovery] tick failed: {e}")
        return 0


def scan_and_resume(limit: int = _SCAN_LIMIT) -> int:
    """一轮扫描(同步核心,供 run_tick 丢线程池,也供测试直调)。返回本轮起跑的工单数。"""
    store.ensure_runtime()
    with db.get_cursor() as cur:
        candidates = _find_candidates(cur, limit=limit)
    resumed = 0
    for row in candidates:
        tenant_id = str(row["tenant_id"])
        work_order_id = str(row["work_order_id"])
        if not feature_flags.pearnly_ai_bank_sales_suggest_enabled_for(tenant_id):
            continue  # 闸现在关着,不越权重跑
        try:
            if _resume_one(tenant_id, work_order_id):
                resumed += 1
        except Exception:  # noqa: BLE001 - 一单失败不连坐下一单
            logger.exception(f"[bank-sales-recovery] resume failed wo={work_order_id}")
    if resumed:
        logger.info(f"[bank-sales-recovery] resumed={resumed}")
    return resumed


def _find_candidates(cur, *, limit: int) -> list[dict]:
    """候选 = 工单 status∈{review,stuck} 且最近一条大脑终态是 failed(某 failed 事件 id 大于
    最新 finished 事件 id)。pending_rows>0 / 重试预算由 _resume_one 逐单精判(需回放事件流,
    不塞进 SQL)。跨租户系统扫描 + 显式 LIMIT 防雪崩。"""
    cur.execute(
        """
        SELECT DISTINCT e.tenant_id, e.work_order_id
        FROM work_order_events e
        JOIN work_orders wo ON wo.id = e.work_order_id AND wo.tenant_id = e.tenant_id
        WHERE e.event_type = %s
          AND wo.status IN (%s, %s)
          AND e.id > COALESCE((
                SELECT max(f.id) FROM work_order_events f
                WHERE f.tenant_id = e.tenant_id
                  AND f.work_order_id = e.work_order_id
                  AND f.event_type = %s), 0)
        LIMIT %s
        """,
        (
            brain.EVT_BRAIN_FAILED,
            engine.STATUS_REVIEW,
            engine.STATUS_STUCK,
            brain.EVT_BRAIN_FINISHED,
            limit,
        ),
    )
    return [dict(r) for r in cur.fetchall()]


def _resume_one(tenant_id: str, work_order_id: str) -> bool:
    """一单:仍有 pending 行 + 自动重试预算未耗尽 → 起后台 run_async(begin_run 抢跨进程租约)。"""
    with db.get_cursor() as cur:
        events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    pending = suggest.pending_rows(events)  # 覆盖不可靠时恒空 → 天然不重跑
    if not pending:
        return False
    if auto_retry_count(events) >= AUTO_RETRY_LIMIT:
        return False  # 重试也熔断:停手等人
    owner = brain.begin_run(tenant_id, work_order_id, len(pending))
    if owner is None:
        return False  # 有人在跑(进程内或跨进程租约),让位
    try:
        threading.Thread(
            target=brain.run_async,
            kwargs={
                "tenant_id": tenant_id,
                "work_order_id": work_order_id,
                "claimed": True,
                "lease_owner": owner,
                "trigger": brain.TRIGGER_RECOVERY,
            },
            daemon=True,
            name=f"bank-sales-recover-{work_order_id[:8]}",
        ).start()
    except Exception:
        brain.fail_start(tenant_id, work_order_id, owner)
        raise
    return True


def auto_retry_count(events: list) -> int:
    """已用掉的自动重试次数 = trigger=recovery 的 bank_sales_brain_failed 事件数(从事件流现算,
    不加列)。人工 /run 触发的失败(trigger=manual)不计——熔断只防无人值守重试烧钱。"""
    return sum(
        1
        for e in events
        if e.get("event_type") == brain.EVT_BRAIN_FAILED
        and (e.get("payload") or {}).get("trigger") == brain.TRIGGER_RECOVERY
    )
