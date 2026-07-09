# -*- coding: utf-8 -*-
"""工单制 HTTP 编排层(routes/workorder_routes 的无框架内核)。

只做「取库 → 现算 → 落事件」的编排,不碰 FastAPI、不判权限、不开事务(cur 由路由注入)。
事件流是唯一事实源:详情/needs/关键数字全部从 events + items 现算,不建影子状态表。
校验错抛 WorkOrderApiError(带 code),路由再翻成 4xx —— 服务层与 HTTP 层解耦,可脱框架测。
"""

from __future__ import annotations

from typing import Optional

from services.workorder import evidence, store

# 人工裁决三态,与 CLI --decide 同语义(见 L2-验收.md):
#   face_value=确认票面 OCR 读数 · recalc=人工看原票补正 · exclude=剔除不计入
_DECISIONS = ("face_value", "recalc", "exclude")
_DECISION_STEP = "reconcile"
_EVT_DECISION = "human_decision"
_EVT_CLASSIFIED = "item_classified"
_EVT_NEEDS = "step_needs"
_EVT_STUCK = "step_stuck"
_STATUS_STUCK = "stuck"

_NUMBER_KEYS = (
    "tax_due",
    "sales_amount",
    "output_vat",
    "purchase_amount",
    "input_vat",
    "period",
    "prior_period_check",
)


class WorkOrderApiError(ValueError):
    """业务级校验错(路由映射成 4xx)。code 给前端错误契约。"""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def open_order(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    period: str,
    intent: str = "monthly_vat",
) -> dict:
    """开单(幂等返回既有单)。归属校验(该账套是否属本租户)由路由先行完成。"""
    return store.open_work_order(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        intent=intent,
    )


def list_orders(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: Optional[int] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    orders = store.list_work_orders(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        status=status,
        limit=limit,
        offset=offset,
    )
    total = store.count_work_orders(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        status=status,
    )
    return {"orders": orders, "count": total, "limit": limit, "offset": offset}


def order_detail(cur, *, tenant_id: str, work_order_id: str) -> Optional[dict]:
    """工单详情:status/current_step + flagged 清单 + needs/停机原因 + 关键数字 + 交付物概览。
    全部从 work_orders 行 + items + events 现算(事件流唯一事实源)。"""
    wo = store.get_work_order(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    if not wo:
        return None
    items = store.list_items(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    deliverables = store.list_deliverables(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    needs, blocked = _halt_info(events, wo["status"])
    return {
        "id": wo["id"],
        "workspace_client_id": wo["workspace_client_id"],
        "period": wo["period"],
        "intent": wo["intent"],
        "status": wo["status"],
        "current_step": wo["current_step"],
        "flagged": _flagged(items, events),
        "needs": needs,
        "blocked_reasons": blocked,
        "numbers": _numbers(events),
        "deliverables": [
            {"kind": d["kind"], "numbers": d.get("numbers") or {}} for d in deliverables
        ],
    }


def _flagged(items: list[dict], events: list[dict]) -> list[dict]:
    """挂起清单 + 每张票的 OCR 读数与最新裁决(W3 审核队列一次喂满,零额外往返)。

    ocr_read = item_classified 的 payload.money(票面钱字段原始串);decision = 该 item
    最新一条 human_decision(latest-wins,与 reconcile 回放同语义)。都可为 None——没读出
    /没判过就诚实给空,不造数据。"""
    classified = evidence.replay_items_by_type(events, _EVT_CLASSIFIED)
    decisions = evidence.replay_items_by_type(events, _EVT_DECISION)
    return [
        {
            "item_id": it["id"],
            "file_ref": it.get("file_ref"),
            "kind": it["kind"],
            "flag_reason": it.get("flag_reason"),
            "ocr_read": (classified.get(it["id"]) or {}).get("payload", {}).get("money"),
            "decision": _decision_of(decisions.get(it["id"])),
        }
        for it in items
        if it["status"] == "flagged"
    ]


def _decision_of(replayed: Optional[dict]) -> Optional[dict]:
    if not replayed:
        return None
    payload = replayed.get("payload") or {}
    return {
        "decision": payload.get("decision"),
        "values": payload.get("values") or {},
        "actor": replayed.get("actor"),
        "at": replayed.get("at"),
    }


def _halt_info(events: list[dict], status: str) -> tuple[list, list]:
    """停机诊断:仅当工单停在 stuck 时,取最后一条停机事件——needs→缺料清单,stuck→卡点原因。"""
    if status != _STATUS_STUCK:
        return [], []
    last = None
    for e in events:
        if e["event_type"] in (_EVT_NEEDS, _EVT_STUCK):
            last = e
    if last is None:
        return [], []
    payload = last.get("payload") or {}
    if last["event_type"] == _EVT_NEEDS:
        return list(payload.get("missing") or []), []
    return [], list(payload.get("reasons") or [])


def _numbers(events: list[dict]) -> dict:
    payload = evidence.replay_step_done(events, "compute") or {}
    return {k: payload.get(k) for k in _NUMBER_KEYS if payload.get(k) is not None}


def record_decision(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    item_id: str,
    decision: str,
    values: Optional[dict],
    actor: str,
) -> dict:
    """落人工裁决事件(CLI --decide 同语义)。校验裁决合法 + item 确属该单,否则拒。"""
    if decision not in _DECISIONS:
        raise WorkOrderApiError("workorder.decision_invalid")
    item = store.get_item(cur, tenant_id=tenant_id, work_order_id=work_order_id, item_id=item_id)
    if not item:
        raise WorkOrderApiError("workorder.item_not_found")
    return store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=_DECISION_STEP,
        event_type=_EVT_DECISION,
        payload={"item_id": item_id, "decision": decision, "values": values or {}},
        actor=actor,
    )


def list_deliverables(cur, *, tenant_id: str, work_order_id: str) -> list[dict]:
    rows = store.list_deliverables(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    return [
        {
            "kind": r["kind"],
            "numbers": r.get("numbers") or {},
            "has_file": bool(r.get("artifact_path")),
        }
        for r in rows
    ]


def deliverable_artifact_path(
    cur, *, tenant_id: str, work_order_id: str, kind: str
) -> Optional[str]:
    """取某类交付物库里登记的 artifact_path(下载用);无则 None。"""
    for r in store.list_deliverables(cur, tenant_id=tenant_id, work_order_id=work_order_id):
        if r["kind"] == kind:
            return r.get("artifact_path")
    return None
