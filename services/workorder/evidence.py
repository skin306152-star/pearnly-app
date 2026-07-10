# -*- coding: utf-8 -*-
"""证据链回放与索引汇编(任务包 §5 步 6)。

work_order_events 只追加,是证据链的唯一底座。本模块零副作用、不碰 store/DB:输入是
已查出来的事件/条目列表,输出是回放结果或证据索引——把「回放」这个动作从各步的
编排里收口成公用函数,compute.py(取 reconcile 数字)与 package.py(出 evidence_index
交付物)共用同一套回放逻辑,不各写一份。不重算任何钱,只做证据的收集与索引。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

_EVT_DONE = "step_done"
_EVT_CLASSIFIED = "item_classified"
_EVT_DECISION = "human_decision"
_KIND_PURCHASE = "purchase_invoice"
_KIND_SALES = "sales_summary"
_KIND_UNKNOWN = "unknown"

# 方向不明票(item_classified.kind=unknown)经人工 assign_kind 裁定为进项后的裁决取值——
# 与 reconcile_gates._apply_direction 同一张表,不重复定义两套 assign_kind 语义。
_DECISION_ASSIGN_KIND = "assign_kind"

# 应缴税额的证据只挂 compute 自己的 step_done——它是"销项-进项"这一步减法的落库点。
_NUMBER_STEP = {"tax_due": "compute"}

# 销项来源标注(状态诚实:人工申报的销项数字不能与 POS 直读的数字混为一谈)。sales_read
# 有 source 字段(api.record_sales_summary 打的 "manual_entry")才是人工;POS xlsx 直读
# (classify.py 的 _classify_summary)不写这个字段,缺省即 direct_read。
_SOURCE_DIRECT = "direct_read"
_SOURCE_MIXED = "mixed"


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
    """按 item_id 回放某类事件为 {item_id: {"event_id":, "payload":, "actor":, "at":}}
    (同 item 多条时后者胜,反映最新裁决/识别——与 reconcile.py 回放同一份事件流的语义
    一致)。actor/at 给「谁在何时判的」读侧(W3 审核队列);老消费者只取 payload 不受影响。"""
    out: dict = {}
    for e in events:
        if e["event_type"] != event_type:
            continue
        payload = e.get("payload") or {}
        item_id = payload.get("item_id")
        if item_id:
            out[item_id] = {
                "event_id": e["id"],
                "payload": payload,
                "actor": e.get("actor"),
                "at": e.get("created_at"),
            }
    return out


def build_evidence_index(
    *,
    work_order_id: str,
    period: Optional[str],
    items: list[dict],
    events: list[dict],
    numbers: dict,
) -> dict:
    """汇编证据索引:每个关键数字 → 支撑它的事件 id 列表 + 原件路径 + item id。

    numbers 传 package 已解得的 {tax_due, sales_amount, output_vat, purchase_amount,
    input_vat}(str(Decimal))。进项相关三个数字(input_vat/purchase_amount 共享同一批
    进项票证据)指向 item_classified(purchase_invoice)+ 对应 human_decision 事件;
    销项两个数字(sales_amount/output_vat)指向 item_classified(sales_summary,status=ok)
    事件,并标注来源(direct_read/manual_entry/mixed,状态诚实不与直读数混淆);tax_due
    指向 compute 的 step_done(无直接原件,items 恒空)。items 供前端点验回链(W5):
    逐条 {item_id, file_name},拿 item_id 直接打 GET /items/{item_id}/image——file_name
    为 None 即该条无原件(如人工填的销项没有票据文件),前端据此诚实降级不裂图。
    """
    files_by_item = {it["id"]: it.get("file_ref") for it in items}
    classified = replay_items_by_type(events, _EVT_CLASSIFIED)
    decisions = replay_items_by_type(events, _EVT_DECISION)

    purchase_evidence = _collect_evidence(
        classified, decisions, files_by_item, _KIND_PURCHASE, include_direction_assigned=True
    )
    sales_evidence = _collect_evidence(classified, decisions, files_by_item, _KIND_SALES)
    sales_source = sales_source_info(classified, decisions)
    compute_done = _compute_done_event(events)

    number_evidence = {}
    for key in ("input_vat", "purchase_amount"):
        if key in numbers:
            number_evidence[key] = {"value": numbers[key], **purchase_evidence}
    for key in ("sales_amount", "output_vat"):
        if key in numbers:
            number_evidence[key] = {"value": numbers[key], **sales_evidence, **sales_source}
    if "tax_due" in numbers:
        number_evidence["tax_due"] = {
            "value": numbers["tax_due"],
            "event_ids": [compute_done["event_id"]] if compute_done else [],
            "source_files": [],
            "items": [],
        }

    return {
        "work_order_id": work_order_id,
        "period": period,
        "numbers": number_evidence,
    }


def _collect_evidence(
    classified: dict,
    decisions: dict,
    files_by_item: dict,
    kind: str,
    *,
    include_direction_assigned: bool = False,
) -> dict:
    """某类 item(购/销)的证据聚合:事件 id / 原件路径各自去重后排序(确定性输出,利于
    快照测试与 diff 复核)+ items 逐条 {item_id, file_name}(item_id 排序,file_name 取
    file_ref 的 basename,没有原件就是 None——前端点验回链据此逐条打开原图或诚实降级)。
    sales 只收 status=ok 的直读(flagged 的销项没有可用数字,不该被列为"支撑证据")。

    include_direction_assigned=True(仅 purchase 调用)时,额外纳入方向不明票:原始
    item_classified.kind 恒为 unknown(reconcile R1 与本函数同口径认它),但已有 assign_kind
    人工裁决把它定向为 kind——这类票的 VAT 已进 input_vat 合计,证据索引不能漏它。事件 id
    同时收 item_classified 与 human_decision 两条(裁决本身也是证据);裁定 non_tax/sales_doc
    的方向票不属于该 kind,不纳入。"""
    event_ids: set = set()
    source_files: set = set()
    file_by_item_id: dict = {}
    for item_id, rec in classified.items():
        payload = rec["payload"]
        dec = decisions.get(item_id)
        direction_assigned = (
            include_direction_assigned
            and payload.get("kind") == _KIND_UNKNOWN
            and dec is not None
            and dec["payload"].get("decision") == _DECISION_ASSIGN_KIND
            and dec["payload"].get("kind") == kind
        )
        if payload.get("kind") != kind and not direction_assigned:
            continue
        if not direction_assigned and kind == _KIND_SALES and payload.get("status") != "ok":
            continue
        if dec and dec["payload"].get("decision") == "exclude":
            continue  # 人工裁决剔除的票没进合计,不算这个数字的支撑证据
        event_ids.add(rec["event_id"])
        file_ref = files_by_item.get(item_id)
        file_by_item_id[item_id] = file_ref
        if file_ref:
            source_files.add(file_ref)
        if dec:
            event_ids.add(dec["event_id"])
    return {
        "event_ids": sorted(event_ids),
        # 仅供 evidence_index.json 审计留痕,前端点验回链只读 items,两字段非镜像不需同步维护。
        "source_files": sorted(source_files),
        "items": [
            {"item_id": iid, "file_name": Path(ref).name if ref else None}
            for iid, ref in sorted(file_by_item_id.items())
        ],
    }


def sales_source_info(classified: dict, decisions: dict) -> dict:
    """销项数字的来源标注:direct_read(POS 导出直读)/ manual_entry(人工填,附凭据备注)/
    mixed(同工单两种来源并存,如实标不各挑一个盖过另一个)。没有任何已生效的销项直读
    (全被剔除或本就没有)返回空字典——package.py/evidence 据此各自诚实降级,不假装有来源。

    唯一判定源:api.record_sales_summary 落的 item_classified(sales_summary).sales_read.
    source == "manual_entry";POS xlsx 直读(classify.py._classify_summary)不写这个字段。
    人工裁决剔除(exclude)的销项件不计入(与 _collect_evidence 的排除口径一致)。

    吃已回放好的 classified/decisions(与 _collect_evidence 一家人)——调用方若手上只有
    events,用下面的 sales_source_info_from_events 薄包装,不要各自重新 replay 一遍。
    """
    sources: set = set()
    notes: list = []
    for item_id, rec in classified.items():
        payload = rec["payload"]
        if payload.get("kind") != _KIND_SALES or payload.get("status") != "ok":
            continue
        dec = decisions.get(item_id)
        if dec and dec["payload"].get("decision") == "exclude":
            continue
        sales_read = payload.get("sales_read") or {}
        sources.add(sales_read.get("source") or _SOURCE_DIRECT)
        note = sales_read.get("note")
        if note:
            notes.append(note)
    if not sources:
        return {}
    info = {"source": next(iter(sources)) if len(sources) == 1 else _SOURCE_MIXED}
    if notes:
        info["note"] = "; ".join(notes)
    return info


def sales_source_info_from_events(events: list[dict]) -> dict:
    """sales_source_info 的薄包装,给拿不到 build_evidence_index 已算好的 classified/
    decisions 的调用方(package.py:_resolve_numbers,数字落定要早于证据索引汇编)用——
    每种事件类型只 replay 一次,不比 sales_source_info 本身多扫。"""
    classified = replay_items_by_type(events, _EVT_CLASSIFIED)
    decisions = replay_items_by_type(events, _EVT_DECISION)
    return sales_source_info(classified, decisions)


def _compute_done_event(events: list[dict]) -> Optional[dict]:
    for e in events:
        if e["event_type"] == _EVT_DONE and e["step"] == "compute":
            return {"event_id": e["id"]}
    return None
