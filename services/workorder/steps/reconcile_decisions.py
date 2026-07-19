# -*- coding: utf-8 -*-
"""人工裁决合并回放(reconcile 取数专用,自 reconcile.py 拆出保 <500)。

方向(assign_kind)与金额裁决(face_value/recalc/exclude/waive)各留最新一条,合到同一记录
——同一件先裁方向再补金额(或反之)不再互相顶掉。SM 2569-05 实锤的单槽死锁:recalc 最新
则方向卡,assign_kind 最新则金额卡,永远出不了包。
形状向后兼容:只有一类裁决时与旧 latest-wins 逐字节同;并存时 decision/values=金额裁决,
kind 恒携带最新方向。
"""

from __future__ import annotations

from services.workorder import decisions

EVT_DECISION = "human_decision"


def replay(events: list[dict]) -> dict:
    """事件流 → {item_id: 合并裁决记录}。"""
    out: dict = {}
    for e in events:
        if e.get("event_type") != EVT_DECISION:
            continue
        p = e.get("payload") or {}
        iid = p.get("item_id")
        if not iid:
            continue
        rec = dict(out.get(iid) or {})
        if p.get("decision") == decisions.ASSIGN_KIND:
            if rec.get("decision") in decisions.NON_COUNTING:
                rec = {}  # 豁免/剔除后又改判方向=改主意,旧的不计入裁决作废
            rec["kind"] = p.get("kind")
            rec.setdefault("decision", decisions.ASSIGN_KIND)
        else:
            rec.update({k: v for k, v in p.items() if k != "item_id"})
        out[iid] = rec
    return out


def kind_of(item: dict, decisions_by_item: dict) -> str:
    """人工方向裁决压过分类 kind,不回写 item 行(kind 槽独立于金额裁决)。"""
    decision = decisions_by_item.get(item["id"]) or {}
    return decision.get("kind") or item["kind"]
