# -*- coding: utf-8 -*-
"""进项票「该推的 ↔ 推过的」只读投影(纯函数,零 I/O)。

reconcile 的推送回执比对(F2-辅)与管家的「这期还有几张没推进 Express」问的是同一个集合:
本工单已采信的进项票逐张,对上 erp_push_logs 里该票号最新那条。两处各算一份迟早漂——同一
家同一期,一边说「都推完了」另一边说「还差三张」,会计无从判断谁错。口径收在本模块一份。

采信口径与 R1 合计同源(reconcile_gates.resolve_input_vat):kind=purchase_invoice 且
status ∈ (ok, flagged),flagged 件被裁成剔除/豁免的不算——它们没进税额合计,自然也不该推。
方向不明票(kind=unknown,靠人工 assign_kind 裁进项)有意不在此列,与既有 F2-辅 口径一致。

查库留给调用方(services.erp.push_log_queries.list_push_logs_by_invoice_nos 是现成的批量
读,一条 SQL 吃整批票号)——本模块只回答两件事:该有哪些票号、一条推送日志算不算推进去了。
"""

from __future__ import annotations

from typing import Optional

from services.workorder import corrections, decisions, kinds

_EVT_CLASSIFIED = "item_classified"
_COUNTED_STATUSES = ("ok", "flagged")

# 一张票在 ERP 那头的落点(erp_push_logs.status → 四态)。
STATE_PUSHED = "pushed"  # success / skipped_dup(判重跳过 = 之前已成功推过,归成功)
STATE_FAILED = "failed"
STATE_IN_FLIGHT = "in_flight"  # pending / retrying / manual:未终态,不冒充任一终态
STATE_NEVER = "never"  # 推送日志里根本没有这张票

_SUCCESS_STATUSES = ("success", "skipped_dup")


def push_state(row: Optional[dict]) -> str:
    """某票号最新那条推送日志 → 四态。查无行是常态不是异常:没推过 ≠ 推失败。"""
    if not row:
        return STATE_NEVER
    status = row.get("status") or ""
    if status in _SUCCESS_STATUSES:
        return STATE_PUSHED
    if status == STATE_FAILED:
        return STATE_FAILED
    return STATE_IN_FLIGHT


def index_by_invoice_no(rows: Optional[list[dict]]) -> dict[str, dict]:
    """推送日志行 → {票号: 行}。DAL 已按票号折叠成最新一条,这里只索引不再折。"""
    return {str(r["invoice_no"]): r for r in (rows or []) if r.get("invoice_no")}


def replay_money(events: Optional[list[dict]]) -> dict:
    """票面钱字段:带 money 载荷的 item_classified 事件按 item_id 回放 latest-wins
    (进项票 + 方向不明票——后者钱已读出,只是进/销还没判准)。"""
    latest: dict = {}
    for e in events or []:
        if e.get("event_type") != _EVT_CLASSIFIED:
            continue
        payload = e.get("payload") or {}
        if payload.get("item_id"):
            latest[payload["item_id"]] = payload
    return {iid: p["money"] for iid, p in latest.items() if p.get("money")}


def counted_purchase_invoices(
    items: Optional[list[dict]], events: Optional[list[dict]]
) -> list[dict]:
    """本工单已采信的进项票逐张(保序 = 件的落库序)。

    每行除票面字段外带两个判据位:item_status(件态)与 awaiting_decision(flagged 且还没
    人裁——这批在 R1 会让 reconcile 停机,当然也还没到能推的时候)。票号读不出的件照样在列:
    「读不出票号」正是漏推的头号成因,静默丢掉等于帮着漏。
    """
    money_by_item = replay_money(events)
    decided = decisions.replay_payloads(events or [])
    out = []
    for it in items or []:
        if it.get("kind") != kinds.PURCHASE_INVOICE or it.get("status") not in _COUNTED_STATUSES:
            continue
        decision = decided.get(it["id"]) or {}
        # 剔除/豁免只在 flagged 件上成立(没 flag 的件没有可裁的东西)——与 R1 合计的采信
        # 口径逐条对齐,不在这里悄悄放宽。
        if it.get("status") == "flagged" and decision.get("decision") in decisions.NON_COUNTING:
            continue
        money = corrections.apply_to_money(money_by_item.get(it["id"]), decision)
        out.append(
            {
                "item_id": it["id"],
                "invoice_no": str(money.get("invoice_number") or "").strip(),
                "invoice_date": money.get("invoice_date") or "",
                "vendor": money.get("vendor") or "",
                "total_amount": money.get("total_amount"),
                "file_ref": it.get("original_name") or it.get("file_ref") or "",
                "item_status": it.get("status") or "",
                "awaiting_decision": it.get("status") == "flagged" and not decision,
            }
        )
    return out


def expected_invoice_nos(items: Optional[list[dict]], events: Optional[list[dict]]) -> list[str]:
    """该推进 ERP 的票号(保序去重,读不出的空号丢弃)。查 erp_push_logs 的入参就是它。"""
    seen: set[str] = set()
    out: list[str] = []
    for row in counted_purchase_invoices(items, events):
        no = row["invoice_no"]
        if no and no not in seen:
            seen.add(no)
            out.append(no)
    return out
