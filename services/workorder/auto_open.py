# -*- coding: utf-8 -*-
"""按税历自动开单(MC2-B 件3)。

挂 background_loops.run_recovery_tick 既有周期巡检(与 reaper/proactive/dunning 等恢复
队列同挂点,禁新 cron)。每日一次(曼谷时区判日界)扫「当期已物化义务、但该期还没开
monthly_vat 工单」的客户 → 逐个 api.open_order(与手动开单同一幂等键:tenant×client×
period×intent,work_orders 唯一索引兜底,重复 tick 天然零重复,不额外造一套幂等机制)。

边界(方案 §「不做」清单 + 派单书裁定):
  · 只开当期(obligation_engine.current_be_period),不追溯历史账期。
  · 只为 pearnly_ai_m1 闸打开的租户开——与画像/矩阵读侧同权,不越权开单(重新查一遍
    闸,不信候选行本身"曾经物化过"就代表闸现在还开着,画像可能是闸开着时存的旧数据)。
  · 不自动跑 OCR(开单落在 collecting 默认态,等人工/LINE 收料,与手动开单初始态一致)。
  · 每 tick 限量 _SCAN_LIMIT 防雪崩,命中上限记 log(下一天再继续扫剩下的)。

「当天已扫过」去重:复用既有 platform_settings 通用 key-value 表(钥匙闸机制原为灰度
开关设计,这里借它的 key→jsonb value 存「最后扫描日期」标记,零新表零新列——选它是因为
它已经是全局非租户表,不必再起一张一次性用途的表)。跨租户系统扫描,与 background_loops
其它恢复队列(services.workorder.reaper.list_dead_runs)同口径——后台任务无单请求租户
上下文,行级隔离靠显式 tenant_id 参数逐单落库,不靠 RLS 游标。
"""

from __future__ import annotations

import asyncio
import logging

from core import db
from core.feature_flags import pearnly_ai_m1_enabled_for
from services.notification import store as notification_store
from services.platform_settings import store as platform_settings_store
from services.workorder import api, engine, obligation_engine, store

logger = logging.getLogger(__name__)

ACTOR_SCHEDULER = "system:scheduler"
EVT_AUTO_OPENED = "order_auto_opened"
_INTENT = "monthly_vat"
_SCAN_LIMIT = 20
_SETTING_KEY = "workorder_auto_open_last_scan"


async def run_tick() -> int:
    """挂点入口(background_loops.run_recovery_tick 周期巡检)。

    日界先判(曼谷时区,今天已扫过直接免费退出,不占位)· 核心扫描丢线程池(同步 DB
    调用不阻塞事件循环,照 reaper.run_tick / posting_failures.retry_due 同款)。「已扫过」
    标记在扫描**成功完成后**才落(不是先标后扫)——扫描本身异常时不占用当天配额,同一
    曼谷日的下一轮 tick 还会重试,不用干等到明天。自吞异常,失败记日志、下一轮巡检
    再试——本挂点不该拖垮同 tick 里其它恢复队列。
    """
    try:
        today_iso = notification_store.bangkok_today().isoformat()
        last = platform_settings_store.get_setting(_SETTING_KEY)
        if last and (last.get("value") or {}).get("date") == today_iso:
            return 0
        opened = await asyncio.to_thread(scan_and_open_due)
        platform_settings_store.set_setting(_SETTING_KEY, {"date": today_iso}, enabled=True)
        return opened
    except Exception as e:  # noqa: BLE001 - 挂点安全,失败记日志下一轮再试
        logger.warning(f"[workorder-auto-open] tick failed: {e}")
        return 0


def scan_and_open_due(limit: int = _SCAN_LIMIT) -> int:
    """一轮扫描(同步核心,供 run_tick 丢线程池,也供测试直调)。

    候选 = period 当期已物化义务、但该期还没有 monthly_vat 工单的 (tenant, client) 对;
    逐个开单,单条失败不连坐(照 reaper.reap_dead_runs 一单一收尸的惯例)。
    """
    period = obligation_engine.current_be_period()
    with db.get_cursor() as cur:
        candidates = _find_candidates(cur, period=period, limit=limit)

    opened = 0
    for row in candidates:
        tenant_id = str(row["tenant_id"])
        if not pearnly_ai_m1_enabled_for(tenant_id, None):
            continue  # 闸现在关着(存量义务可能是闸曾开时存的),不越权开单
        try:
            _open_one(tenant_id, int(row["workspace_client_id"]), period)
            opened += 1
        except Exception:
            logger.exception(
                "[workorder-auto-open] open failed tenant=%s client=%s period=%s",
                tenant_id,
                row["workspace_client_id"],
                period,
            )
    if opened:
        logger.info(f"[workorder-auto-open] period={period} opened={opened}")
    if len(candidates) >= limit:
        logger.warning(f"[workorder-auto-open] hit scan limit={limit} period={period}")
    return opened


def _find_candidates(cur, *, period: str, limit: int) -> list[dict]:
    """跨租户系统扫描(见模块顶注理由),显式 LIMIT 防雪崩。"""
    cur.execute(
        """
        SELECT DISTINCT o.tenant_id, o.workspace_client_id
        FROM client_period_obligations o
        LEFT JOIN work_orders wo
            ON wo.tenant_id = o.tenant_id
           AND wo.workspace_client_id = o.workspace_client_id
           AND wo.period = o.period
           AND wo.intent = %s
        WHERE o.period = %s
          AND wo.id IS NULL
        LIMIT %s
        """,
        (_INTENT, period, limit),
    )
    return [dict(r) for r in cur.fetchall()]


def _open_one(tenant_id: str, workspace_client_id: int, period: str) -> None:
    """开单(复用 api.open_order 的幂等键,重复调用零副作用)+ 落一条 actor=system:scheduler
    的审计事件(dedupe_key 按 period 幂等,同一张单不会因反复扫描重复记两条)。"""
    with db.get_cursor(commit=True) as cur:
        wo = api.open_order(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            period=period,
            intent=_INTENT,
        )
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=wo["id"],
            step=engine.STEPS[0],
            event_type=EVT_AUTO_OPENED,
            payload={"period": period},
            actor=ACTOR_SCHEDULER,
            dedupe_key=f"auto_open:{period}",
        )
