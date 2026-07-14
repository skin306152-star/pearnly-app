# -*- coding: utf-8 -*-
"""证据链回放与索引汇编(任务包 §5 步 6)。

work_order_events 只追加,是证据链的唯一底座。本模块零副作用、不碰 store/DB:输入是
已查出来的事件/条目列表,输出是回放结果或证据索引——把「回放」这个动作从各步的
编排里收口成公用函数,compute.py(取 reconcile 数字)与 package.py(出 evidence_index
交付物)共用同一套回放逻辑,不各写一份。不重算任何钱,只做证据的收集与索引。

「冻结值 vs 现算,分叉标 stale」的写读归一(frozen_or_live_corroboration)也收在这:
它是证据消费口径,sales_aggregate 与 edc_corroboration 两处佐证共用,防第三份复写。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from services.workorder import decisions, kinds, verdict

_EVT_DONE = "step_done"
_EVT_CLASSIFIED = "item_classified"
_EVT_DECISION = "human_decision"
_KIND_PURCHASE = kinds.PURCHASE_INVOICE
_KIND_SALES = kinds.SALES_SUMMARY
_KIND_UNKNOWN = kinds.UNKNOWN

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


def frozen_or_live_corroboration(
    events: list[dict],
    *,
    step: str,
    gate_key: str,
    live: Optional[dict],
    compare_keys: tuple,
) -> Optional[dict]:
    """佐证读侧写读归一通用范式(c.1 销项逐票佐证 / SA-2b EDC 聚合佐证同款):优先消费
    step 落库的 step_done.gates[gate_key] 冻结值;未跑到该步时回退现算 live。

    冻结值在场且与现算在 compare_keys 核心钱字段上分叉(算法演进,或 reconcile 后又
    补料)→ 以冻结值为准并标 stale=True,诚实呈现「这是交付那一刻的值」,不静默糊成
    一个数。两处调用方共用同一份归一逻辑,不各写一份。"""
    payload = replay_step_done(events, step)
    frozen = (payload.get("gates") or {}).get(gate_key) if payload else None
    frozen = frozen if isinstance(frozen, dict) else None
    if frozen is None:
        return live
    if live is not None and any(frozen.get(k) != live.get(k) for k in compare_keys):
        return dict(frozen, stale=True)
    return frozen


def bank_recon_from_step_done(payload: Optional[dict]) -> Optional[dict]:
    """从 reconcile 步 step_done 的 payload 深取 R3 银行对账 recon(gates.r3_bank.recon)。

    闸关 / 无银行流水 / 引擎异常降级(_run_bank_recon 落的 {error,note} 残影,无 auto_matched)
    一律给 None。纯函数,不认 payload 从何来——api.bank_recon_raw(全量回放取 payload)与
    bank_recon_review(store 窄取 step_done payload)共用同一份判定,单一事实源不各写一份。"""
    if not payload:
        return None
    recon = ((payload.get("gates") or {}).get("r3_bank") or {}).get("recon")
    return recon if isinstance(recon, dict) and "auto_matched" in recon else None


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


def flagged_projection(
    items: list[dict], events: list[dict], classified: Optional[dict] = None
) -> list[dict]:
    """挂起清单投影(W3 审核队列 + order-detail 一次喂满,零额外往返)。每张 flagged 票带
    OCR 读数、最新裁决、判据人话 + 置信度(verdict_hint · MC1-b1 纯读侧现算,不改引擎不落库)。

    ocr_read = item_classified 的 payload.money(票面钱字段原始串);decision = 该 item 最新一条
    human_decision(latest-wins,与 reconcile 回放同语义);verdict_hint = verdict.hint(flag_reason,
    ocr_read)。都可为 None/空 —— 没读出/没判过就诚实给空,不造数据。classified 可由调用方
    (api.order_detail)传入已回放好的索引,同一请求不重复扫事件流;缺省自算。"""
    if classified is None:
        classified = replay_items_by_type(events, _EVT_CLASSIFIED)
    decisions_by_item = replay_items_by_type(events, _EVT_DECISION)
    out = []
    for it in items:
        if it["status"] != "flagged":
            continue
        ocr_read = (classified.get(it["id"]) or {}).get("payload", {}).get("money")
        out.append(
            {
                "item_id": it["id"],
                "file_ref": it.get("file_ref"),
                "kind": it["kind"],
                "flag_reason": it.get("flag_reason"),
                "ocr_read": ocr_read,
                "decision": _decision_of(decisions_by_item.get(it["id"])),
                "verdict_hint": verdict.hint(flag_reason=it.get("flag_reason"), ocr_read=ocr_read),
            }
        )
    return out


def bank_recon_decisions(events: list[dict]) -> dict:
    """银行对账人审裁决回放(MC1-b3 · E2 债 · statement_tx_id → 裁决摘要,latest-wins)。

    与 replay_items_by_type 同族但键是 statement_tx_id 不是 item_id——银行流水行不是
    work_order_item,没有 items 表身份(见 services/recon/workorder_recon_adapter 的
    statement_tx_id = StatementRow.row_hash 内容指纹)。human_decision 事件按有无
    statement_tx_id/item_id 天然互斥(assign 类裁决走 item_id,银行裁决走 statement_tx_id),
    这里只收后者。供 api._bank_recon 覆盖到 R3 呈现层,一行不碰 R1/R2/R4 税额路径。"""
    out: dict = {}
    for e in events:
        if e["event_type"] != _EVT_DECISION:
            continue
        payload = e.get("payload") or {}
        tx_id = payload.get("statement_tx_id")
        if not tx_id:
            continue
        out[tx_id] = {
            "decision": payload.get("decision"),
            "candidate_id": payload.get("candidate_id"),
            "actor": e.get("actor"),
            "at": e.get("created_at"),
        }
    return out


def _decision_of(replayed: Optional[dict]) -> Optional[dict]:
    """一条 human_decision 回放 → 裁决摘要({decision, kind, values, actor, at});无则 None。
    kind 是方向裁决(assign_kind)携带的裁定 kind,普通裁决为 None。"""
    if not replayed:
        return None
    payload = replayed.get("payload") or {}
    return {
        "decision": payload.get("decision"),
        "kind": payload.get("kind"),
        "values": payload.get("values") or {},
        "actor": replayed.get("actor"),
        "at": replayed.get("at"),
    }


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
    decisions_by_item = replay_items_by_type(events, _EVT_DECISION)

    purchase_evidence = _collect_evidence(
        classified,
        decisions_by_item,
        files_by_item,
        _KIND_PURCHASE,
        include_direction_assigned=True,
    )
    sales_evidence = _collect_evidence(classified, decisions_by_item, files_by_item, _KIND_SALES)
    sales_source = sales_source_info(classified, decisions_by_item)
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
    decisions_by_item: dict,
    files_by_item: dict,
    kind: str,
    *,
    include_direction_assigned: bool = False,
) -> dict:
    """某类 item(购/销)的证据聚合:事件 id / 原件路径各自去重后排序(确定性输出,利于
    快照测试与 diff 复核)+ items 逐条 {item_id, file_name}(item_id 排序,file_name 取
    file_ref 的 basename,没有原件就是 None——前端点验回链据此逐条打开原图或诚实降级)。
    sales 只收 status=ok 的直读(flagged 的销项没有可用数字,不该被列为"支撑证据")。

    include_direction_assigned=True(仅 purchase 调用)时,额外纳入被改判进项的票:原始
    item_classified.kind 是 unknown(方向不明票)或 sales_doc(MC1-c.1 自动判本方销项票),但已有
    assign_kind 人工裁决把它改判为 kind——这类票的 VAT 已进 input_vat 合计(reconcile R1 同口径),
    证据索引不能漏它。事件 id 同时收 item_classified 与 human_decision 两条(裁决本身也是证据);
    裁定 non_tax/sales_doc 的票不属于该 kind,不纳入。"""
    event_ids: set = set()
    source_files: set = set()
    file_by_item_id: dict = {}
    for item_id, rec in classified.items():
        payload = rec["payload"]
        dec = decisions_by_item.get(item_id)
        direction_assigned = (
            include_direction_assigned
            and payload.get("kind") in (_KIND_UNKNOWN, decisions.SALES_DOC)
            and dec is not None
            and dec["payload"].get("decision") == decisions.ASSIGN_KIND
            and dec["payload"].get("kind") == kind
        )
        if payload.get("kind") != kind and not direction_assigned:
            continue
        if not direction_assigned and kind == _KIND_SALES and payload.get("status") != "ok":
            continue
        if dec and dec["payload"].get("decision") in decisions.NON_COUNTING:
            continue  # 剔除/豁免的票没进合计,不算这个数字的支撑证据(豁免留痕在备忘)
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


def sales_source_info(classified: dict, decisions_by_item: dict) -> dict:
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
        dec = decisions_by_item.get(item_id)
        if dec and dec["payload"].get("decision") == decisions.EXCLUDE:
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
    decisions_by_item = replay_items_by_type(events, _EVT_DECISION)
    return sales_source_info(classified, decisions_by_item)


def _compute_done_event(events: list[dict]) -> Optional[dict]:
    for e in events:
        if e["event_type"] == _EVT_DONE and e["step"] == "compute":
            return {"event_id": e["id"]}
    return None
