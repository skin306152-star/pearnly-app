# -*- coding: utf-8 -*-
"""职责分离(SoD)判定 · 工单四权分立(C3 · `pearnly_ai_sod` 闸)。

零依赖(同 decisions.py 惯例):纯从已查出的事件流现算,不碰 DB、不 import 本包其余模块、
不抛 WorkOrderApiError(那属编排层 api.py/archive.py——判定与报错分离,调用方按返回的
违规码自行包成 WorkOrderApiError,避免 sod↔api 循环 import)。

flag 关(enforced=False)时两个 violation 函数恒返回 None——一人所全兼零特判,行为逐字节
走现状单人流。flag 开(事务所)时:
  - 复核签批人不得是制单人(reviewer_violation)。
  - 冻结授权人不得是制单人,且须已有一条签批人∉制单集的有效复核签批(approver_violation)。

制单集从事件流回放得来(与工单其余证据链同一事实源,不落影子标记):往这张单里注入过
人工判断的人 = human_decision(裁决)+ item_classified(sales_summary,人工填销项)的
actor 去重集合。跑引擎(run_requested)是机械触发,不计入——点了个按钮不算制单判断。
"""

from __future__ import annotations

from typing import Optional

_EVT_DECISION = "human_decision"
_EVT_CLASSIFIED = "item_classified"
_EVT_REVIEW_SIGNOFF = "review_signoff"
_KIND_SALES = "sales_summary"

REVIEWER_IS_PREPARER = "workorder.sod.reviewer_is_preparer"
APPROVER_IS_PREPARER = "workorder.sod.approver_is_preparer"
REVIEW_REQUIRED = "workorder.sod.review_required"


def preparer_actors(events: list[dict]) -> set[str]:
    """制单集:裁决(human_decision)与人工填销项(item_classified.kind=sales_summary)
    的 actor 去重。"""
    actors: set[str] = set()
    for e in events:
        actor = e.get("actor")
        if not actor:
            continue
        etype = e.get("event_type")
        if etype == _EVT_DECISION:
            actors.add(actor)
        elif etype == _EVT_CLASSIFIED and (e.get("payload") or {}).get("kind") == _KIND_SALES:
            actors.add(actor)
    return actors


def reviewer_actors(events: list[dict]) -> set[str]:
    """已签批复核人集合(review_signoff 事件的 actor)。"""
    return {
        e["actor"] for e in events if e.get("event_type") == _EVT_REVIEW_SIGNOFF and e.get("actor")
    }


def reviewer_violation(events: list[dict], actor: str, *, enforced: bool) -> Optional[str]:
    """复核签批闸判定。关恒放行;开时复核人不得是制单人。"""
    if not enforced:
        return None
    if actor in preparer_actors(events):
        return REVIEWER_IS_PREPARER
    return None


def approver_violation(events: list[dict], actor: str, *, enforced: bool) -> Optional[str]:
    """冻结授权闸判定。关恒放行;开时授权人不得是制单人,且须已有一条签批人∉制单集的
    有效复核签批(签批人本身若也在制单集内,不算数——不能自审自签绕过闸)。"""
    if not enforced:
        return None
    preparers = preparer_actors(events)
    if actor in preparers:
        return APPROVER_IS_PREPARER
    if not (reviewer_actors(events) - preparers):
        return REVIEW_REQUIRED
    return None
