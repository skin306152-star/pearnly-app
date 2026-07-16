# -*- coding: utf-8 -*-
"""税号重锚(R4 · 高敏,契约收窄)。

守护闸(taxid_alert)点名「登记税号疑似录错」后,会计把账套登记税号改成票上真税号,再调本模块
重锚:把本单无人工裁决的方向不明件(flag_reason 以 direction_ambiguous/sales_direction_unhandled
开头)重置回 pending(kind→unknown)供重判,并重开 classify→package 令引擎重跑;已裁决件绝不动
(人的裁决高于机器)。落 taxid_realign_requested 事件(解除对应警示 + 审计留痕)。

重跑由调用方(路由)以推进原语 request_run 驱动,有跨单去重(R2B)零 OCR 成本。从 api.py 分出
守单文件 <500 行铁律 + 单一职责;reset DAL 与编排同域收在此(run_leases 同款「域自带 DAL」先例)。
"""

from __future__ import annotations

from services.workorder import api, decisions, engine, evidence, kinds, store


def realign(
    cur, *, tenant_id: str, work_order_id: str, registered: str, suspected: str, actor: str
) -> dict:
    """重锚编排:校验确有匹配嫌疑(防臆造重锚误解除告警/污染流)→ 重置无裁决方向不明件 →
    重开 classify→package → 落 taxid_realign_requested。Σ桶=N 守恒:只在方向桶↔进/销桶间搬件,
    总件数不变。重置与重开同事务原子提交;返回复位件数。"""
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not _matching_suspicion(events, registered, suspected):
        raise api.WorkOrderApiError("workorder.taxid_no_suspicion")
    items = store.list_items(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    decided = set(evidence.replay_items_by_type(events, "human_decision").keys())
    reset_ids = [
        it["id"]
        for it in items
        if str(it.get("flag_reason") or "").startswith(decisions.DIRECTION_PREFIXES)
        and it["id"] not in decided
    ]
    if reset_ids:
        _reset_items(cur, tenant_id=tenant_id, work_order_id=work_order_id, item_ids=reset_ids)
        _reopen_from_classify(cur, tenant_id=tenant_id, work_order_id=work_order_id, actor=actor)
    store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step="classify",
        event_type=evidence.EVT_TAXID_REALIGN_REQUESTED,
        payload={
            "registered": registered,
            "suspected": suspected,
            "reset_count": len(reset_ids),
            "reset_item_ids": reset_ids,
        },
        actor=actor,
        dedupe_key=f"taxid_realign:{work_order_id}:{registered}:{suspected}",
    )
    return {"reset_count": len(reset_ids)}


def _matching_suspicion(events: list[dict], registered: str, suspected: str) -> bool:
    """事件流是否确有匹配的 taxid_typo_suspected 嫌疑(校验重锚请求合法)。"""
    for e in events:
        if e["event_type"] == evidence.EVT_TAXID_TYPO_SUSPECTED:
            payload = e.get("payload") or {}
            if payload.get("registered") == registered and payload.get("suspected") == suspected:
                return True
    return False


def _reset_items(cur, *, tenant_id: str, work_order_id: str, item_ids: list) -> int:
    """把指定件重置回 pending(kind→unknown / flag_reason→NULL)供重判。只动传入的「无裁决
    方向不明件」id 集(归属由 realign 收窄);update_item 跳 None 不能清 flag_reason,故直写 NULL
    (与 store.reset_quota_deferred_items 同款)。返回复位件数。"""
    if not item_ids:
        return 0
    cur.execute(
        "UPDATE work_order_items SET status = 'pending', kind = %s, flag_reason = NULL, "
        "updated_at = now() WHERE tenant_id = %s AND work_order_id = %s AND id::text = ANY(%s)",
        (kinds.UNKNOWN, tenant_id, work_order_id, [str(i) for i in item_ids]),
    )
    return cur.rowcount


def _reopen_from_classify(cur, *, tenant_id: str, work_order_id: str, actor: str) -> None:
    """重开 classify→package(撤销其 step_done),令引擎重跑 classify 重判重置件(append-only,
    与驳回重做同语义)。step/词汇取 engine 权威常量,不臆造。"""
    for step in engine.reopen_steps_from("classify"):
        store.append_event(
            cur,
            tenant_id=tenant_id,
            work_order_id=work_order_id,
            step=step,
            event_type=engine.EVT_REOPENED,
            payload={"cause": "taxid_realign"},
            actor=actor,
        )
