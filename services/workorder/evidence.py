# -*- coding: utf-8 -*-
"""证据链回放与索引汇编(任务包 §5 步 6)。

work_order_events 只追加,是证据链的唯一底座。本模块零副作用、不碰 store/DB:输入是
已查出来的事件/条目列表,输出是回放结果或证据索引——把「回放」这个动作从各步的
编排里收口成公用函数,compute.py(取 reconcile 数字)与 package.py(出 evidence_index
交付物)共用同一套回放逻辑,不各写一份。不重算任何钱,只做证据的收集与索引。
"""

from __future__ import annotations

from typing import Optional

_EVT_DONE = "step_done"
_EVT_CLASSIFIED = "item_classified"
_EVT_DECISION = "human_decision"
_KIND_PURCHASE = "purchase_invoice"
_KIND_SALES = "sales_summary"

# 应缴税额的证据只挂 compute 自己的 step_done——它是"销项-进项"这一步减法的落库点。
_NUMBER_STEP = {"tax_due": "compute"}


def replay_step_done(events: list[dict], step: str) -> Optional[dict]:
    """回放某步最后一条 step_done 的 payload。同一步理论上只会 done 一次,取最后一条是
    防御性写法(容忍事件流里出现非常规重复)。没有则返回 None——续跑读不到就该诚实说
    「查不到」,不能拿空字典冒充"已完成"。"""
    payload = None
    for e in events:
        if e["event_type"] == _EVT_DONE and e["step"] == step:
            payload = e.get("payload") or {}
    return payload


def replay_items_by_type(events: list[dict], event_type: str) -> dict:
    """按 item_id 回放某类事件为 {item_id: {"event_id":, "payload":}}(同 item 多条时
    后者胜,反映最新裁决/识别——与 reconcile.py 回放同一份事件流的语义一致)。"""
    out: dict = {}
    for e in events:
        if e["event_type"] != event_type:
            continue
        payload = e.get("payload") or {}
        item_id = payload.get("item_id")
        if item_id:
            out[item_id] = {"event_id": e["id"], "payload": payload}
    return out


def build_evidence_index(
    *,
    work_order_id: str,
    period: Optional[str],
    items: list[dict],
    events: list[dict],
    numbers: dict,
) -> dict:
    """汇编证据索引:每个关键数字 → 支撑它的事件 id 列表 + 原件路径。

    numbers 传 package 已解得的 {tax_due, sales_amount, output_vat, purchase_amount,
    input_vat}(str(Decimal))。进项相关三个数字(input_vat/purchase_amount 共享同一批
    进项票证据)指向 item_classified(purchase_invoice)+ 对应 human_decision 事件;
    销项两个数字(sales_amount/output_vat)指向 item_classified(sales_summary,status=ok)
    事件;tax_due 指向 compute 的 step_done。原件路径取自 work_order_items.file_ref。
    """
    files_by_item = {it["id"]: it.get("file_ref") for it in items}
    classified = replay_items_by_type(events, _EVT_CLASSIFIED)
    decisions = replay_items_by_type(events, _EVT_DECISION)

    purchase_evidence = _collect_evidence(classified, decisions, files_by_item, _KIND_PURCHASE)
    sales_evidence = _collect_evidence(classified, decisions, files_by_item, _KIND_SALES)
    compute_done = _compute_done_event(events)

    number_evidence = {}
    for key in ("input_vat", "purchase_amount"):
        if key in numbers:
            number_evidence[key] = {"value": numbers[key], **purchase_evidence}
    for key in ("sales_amount", "output_vat"):
        if key in numbers:
            number_evidence[key] = {"value": numbers[key], **sales_evidence}
    if "tax_due" in numbers:
        number_evidence["tax_due"] = {
            "value": numbers["tax_due"],
            "event_ids": [compute_done["event_id"]] if compute_done else [],
            "source_files": [],
        }

    return {
        "work_order_id": work_order_id,
        "period": period,
        "numbers": number_evidence,
    }


def _collect_evidence(classified: dict, decisions: dict, files_by_item: dict, kind: str) -> dict:
    """某类 item(购/销)的证据聚合:事件 id 去重后排序、原件路径去重后排序(确定性输出,
    利于快照测试与 diff 复核)。sales 只收 status=ok 的直读(flagged 的销项没有可用数字,
    不该被列为"支撑证据")。"""
    event_ids: set = set()
    source_files: set = set()
    for item_id, rec in classified.items():
        payload = rec["payload"]
        if payload.get("kind") != kind:
            continue
        if kind == _KIND_SALES and payload.get("status") != "ok":
            continue
        dec = decisions.get(item_id)
        if dec and dec["payload"].get("decision") == "exclude":
            continue  # 人工裁决剔除的票没进合计,不算这个数字的支撑证据
        event_ids.add(rec["event_id"])
        file_ref = files_by_item.get(item_id)
        if file_ref:
            source_files.add(file_ref)
        if dec:
            event_ids.add(dec["event_id"])
    return {"event_ids": sorted(event_ids), "source_files": sorted(source_files)}


def _compute_done_event(events: list[dict]) -> Optional[dict]:
    for e in events:
        if e["event_type"] == _EVT_DONE and e["step"] == "compute":
            return {"event_id": e["id"]}
    return None
