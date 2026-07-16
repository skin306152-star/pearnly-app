# -*- coding: utf-8 -*-
"""税号错录守护闸接线(classify 步末尾聚合 → 落工单级警示事件 · R4)。

taxid_guard.suspect_registered_typo 是纯判断(检测),本模块把它接到 classify:分类跑完后
跨料聚合本单全部票面税号(item_classified 事件 money 快照的 seller_tax + buyer_tax,含重复=
支持度信号,勿去重),喂守护闸;命中「登记税号疑似录错」就落一条 taxid_typo_suspected 工单级
事件,供 order_detail.alerts 投影弹卡「票上都是 X,登记 Y,改吗?」。

零副作用于钱:只读事件流 + 落一条警示事件,绝不改任何 item 的钱/堆/态。dedupe_key 锚工单+
登记税号+嫌疑税号,同一嫌疑重跑不重复告警。
"""

from __future__ import annotations

from typing import Optional

from services.workorder import evidence, taxid_guard  # evidence: 警示事件词汇单一事实源

# item_classified 是存量事件词(evidence/reconcile/classify 均用),本模块只读回放不新增语义;
# 新增词(taxid_typo_suspected)单一事实源在 evidence,不在此散落。
_EVT_CLASSIFIED = "item_classified"
_STEP = "classify"


def collect_doc_tax_ids(events: list[dict]) -> list[str]:
    """本单全部票面税号(seller_tax + buyer_tax),含重复——重复即支持度,原样喂守护闸不去重。

    从 item_classified 事件的 money 快照取(reconcile 回放的同一持久源,续跑安全):自家为卖方
    的销项票 seller_tax=自家、自家为买方的进项票 buyer_tax=自家,登记税号敲错时这个真税号会在
    够多张票上反复出现,正是守护闸要抓的锚。同 item 多条取最后一条(latest-wins,反映最新识别)。"""
    latest_money: dict = {}
    for e in events:
        if e.get("event_type") != _EVT_CLASSIFIED:
            continue
        payload = e.get("payload") or {}
        item_id, money = payload.get("item_id"), payload.get("money")
        if item_id and money:
            latest_money[item_id] = money
    out: list[str] = []
    for money in latest_money.values():
        for key in ("seller_tax", "buyer_tax"):
            value = money.get(key)
            if value:
                out.append(value)
    return out


def evaluate(
    registered_tax_id: Optional[str], events: list[dict]
) -> Optional[taxid_guard.TaxIdTypoSuspicion]:
    """跨料聚合判「登记税号疑似录错」。无登记税号 / 无嫌疑 → None(守护闸既有金标不动)。"""
    if not registered_tax_id:
        return None
    return taxid_guard.suspect_registered_typo(registered_tax_id, collect_doc_tax_ids(events))


def flag_if_suspected(ctx, registered_tax_id: Optional[str]) -> Optional[dict]:
    """classify 步末尾挂点:命中嫌疑就落 taxid_typo_suspected 工单级事件,返回落库事件行
    (无嫌疑返 None)。走 ctx.cur 同步骤事务,随 classify 的 step_done 一并提交/回滚。"""
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    suspicion = evaluate(registered_tax_id, events)
    if suspicion is None:
        return None
    return ctx.store.append_event(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        step=_STEP,
        event_type=evidence.EVT_TAXID_TYPO_SUSPECTED,
        payload={
            "registered": suspicion.registered,
            "suspected": suspicion.suspected,
            "doc_count": suspicion.doc_count,
            "distance": suspicion.distance,
            "kind": suspicion.kind,
        },
        dedupe_key=f"taxid_typo:{ctx.work_order_id}:{suspicion.registered}:{suspicion.suspected}",
    )
