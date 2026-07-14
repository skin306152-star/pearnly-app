# -*- coding: utf-8 -*-
"""收件箱 item 级 flagged feed + SoD 投影读模型(MC2-A3 · F1/F9 根治)。

拆出独立于 review.py(队列聚合 + 写动作)是单一职责 + <500 铁律:本模块只做「把待审队列
里各工单的 flagged 明细与职责分离(SoD)状态一次现算好」这一件读侧投影,零写入。

根治 F1(浏览器 N+1):此前前端对每张 flagged 工单各发一次 order_detail(全量事件回放),
全所收件箱一开就是 flagged 工单数 × 重型回放。这里改成随队列长度线性的两次批量取库
(事件 + flagged 件各一条 SQL,列表 = ANY 一把捞),Python 按工单分组回放,前端纯渲染。
flagged 投影本身仍走 evidence.flagged_projection(读值/裁决/判据人话单一事实源不另写一份)。

根治 F9(SoD reactive→proactive):队列行带制单人/复核人/自审投影,前端据此显隐签批钮
(不再让 preparer 白点一次撞 422),后端 archive/signoff 仍是权威闸——本投影只回答「这个
登录态在这张单上是不是制单人 / 有没有独立复核 / 自己声明过没」,判定口径与 sod.py 同源。
"""

from __future__ import annotations

from typing import Optional

from services.workorder import evidence, sod

_EVENTS_SQL = """
SELECT id, work_order_id, step, event_type, payload, actor, created_at
FROM work_order_events
WHERE tenant_id = %s AND work_order_id = ANY(%s::uuid[])
ORDER BY work_order_id, id
"""

_FLAGGED_ITEMS_SQL = """
SELECT id, work_order_id, kind, file_ref, flag_reason, status
FROM work_order_items
WHERE tenant_id = %s AND work_order_id = ANY(%s::uuid[]) AND status = 'flagged'
ORDER BY work_order_id, created_at
"""


def enrich(
    cur,
    *,
    tenant_id: str,
    orders: list[dict],
    actor: Optional[str],
    sod_enforced: bool,
    severity: Optional[str] = None,
) -> list[dict]:
    """给队列内工单挂 SoD 投影(就地写 order['sod']),并返回跨工单扁平 flagged item feed。

    两次批量取库(不随工单数增长):事件按全部队列工单捞(SoD 每张单都要)、flagged 件只按有
    flagged 的工单捞。severity 传入则 feed 只留该严重度的件(与队列分组筛口径一致)。"""
    if not orders:
        return []
    order_ids = [o["work_order_id"] for o in orders]
    events_by_order = _group_by_order(_query(cur, _EVENTS_SQL, tenant_id, order_ids))
    flagged_ids = [o["work_order_id"] for o in orders if o["flagged_total"] > 0]
    items_by_order = (
        _group_by_order(_query(cur, _FLAGGED_ITEMS_SQL, tenant_id, flagged_ids))
        if flagged_ids
        else {}
    )

    feed: list[dict] = []
    for order in orders:
        wid = order["work_order_id"]
        events = events_by_order.get(wid, [])
        order["sod"] = sod_projection(events, actor, sod_enforced)
        if order["flagged_total"] <= 0:
            continue
        projection = evidence.flagged_projection(items_by_order.get(wid, []), events)
        _annotate_undecided(order.get("flagged_groups") or [], projection)
        for item in projection:
            if severity and (item.get("verdict_hint") or {}).get("severity") != severity:
                continue
            item["work_order_id"] = wid
            item["client_name"] = order["client_name"]
            item["period"] = order["period"]
            feed.append(item)
    return feed


def _annotate_undecided(groups: list[dict], projection: list[dict]) -> None:
    """队列头徽章的未决数(2026-07-14 清单 #4):裁决只落 human_decision 事件,item.status
    仍是 flagged,引擎重跑前队列 SQL 的 flagged 计数不会掉——按投影里每件最新裁决现算已裁数,
    徽章组补 decided_count/undecided_count,前端据此不把已裁的计入徽章数字。"""
    decided: dict = {}
    for item in projection:
        if item.get("decision"):
            reason = item.get("flag_reason")
            decided[reason] = decided.get(reason, 0) + 1
    for g in groups:
        g["decided_count"] = decided.get(g["flag_reason"], 0)
        g["undecided_count"] = max(int(g.get("count") or 0) - g["decided_count"], 0)


def sod_projection(events: list[dict], actor: Optional[str], enforced: bool) -> dict:
    """职责分离读侧投影(纯函数):enforced 是否强制 + 登录态在这张单上的三态。判定口径与
    sod.py 权威闸同源(制单集/复核集/自审声明回放),前端据此 proactive 显隐,不复算政策。"""
    preparers = sod.preparer_actors(events)
    reviewers = sod.reviewer_actors(events)
    return {
        "enforced": enforced,
        "is_preparer": bool(actor) and actor in preparers,
        "has_independent_review": bool(reviewers - preparers),
        "self_declared": bool(actor) and sod.self_review_declared_by(events, actor),
    }


def _query(cur, sql: str, tenant_id: str, order_ids: list) -> list[dict]:
    cur.execute(sql, (tenant_id, order_ids))
    return [dict(r) for r in cur.fetchall()]


def _group_by_order(rows: list[dict]) -> dict:
    out: dict = {}
    for r in rows:
        out.setdefault(r["work_order_id"], []).append(r)
    return out
