# -*- coding: utf-8 -*-
"""工单制 HTTP 编排层(routes/workorder_routes 的无框架内核)。

只做「取库 → 现算 → 落事件」的编排,不碰 FastAPI、不判权限、不开事务(cur 由路由注入)。
事件流是唯一事实源:详情/needs/关键数字全部从 events + items 现算,不建影子状态表。
校验错抛 WorkOrderApiError(带 code),路由再翻成 4xx —— 服务层与 HTTP 层解耦,可脱框架测。
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Optional

from core.feature_flags import pearnly_ai_m1_enabled_for
from services.workorder import decisions, evidence, obligation_engine, store
from services.workspace import tax_profile_store

logger = logging.getLogger(__name__)

# 人工裁决三态,与 CLI --decide 同语义(见 L2-验收.md):
#   face_value=确认票面 OCR 读数 · recalc=人工看原票补正 · exclude=剔除不计入
_DECISIONS = (decisions.FACE_VALUE, decisions.RECALC, decisions.EXCLUDE)
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

# 人工填销项(W4 补料流)常量。落一条与 classify 直读同构的 item_classified(sales_summary)
# 事件,reconcile 的 _replay_sales_reads/aggregate_sales 原样回放解锁 R2——引擎/steps 不改一行。
_SALES_KIND = "sales_summary"
_MANUAL_SOURCE = "manual"
_MANUAL_SALES_DEDUPE = "manual:sales_summary"
_MAX_NOTE_LEN = 500
# reconcile.aggregate_sales 靠表头关键词认「销售额列 / 销项税列」;人工填的两个合计以泰文规范
# 列名 + 单数据行合成表落库,与真实 POS 汇总表直读产出的 sales_read 形状一致(不另造契约)。
_SALES_HEADER = "ยอดขาย"
_OUTPUT_VAT_HEADER = "ภาษีขาย"


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
    wo = store.open_work_order(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        intent=intent,
    )
    if pearnly_ai_m1_enabled_for(tenant_id, None):
        _generate_obligations_on_open(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            work_order_id=wo["id"],
            period=period,
        )
    return wo


def _generate_obligations_on_open(
    cur, *, tenant_id: str, workspace_client_id: int, work_order_id: str, period: str
) -> None:
    """开单即生成一次当期义务清单(税务画像-方案-B1.md §3 · B2-d)。数据信号本批传空
    (TODO(D1):扫采购行 WHT/境外付款/利息股息付款出真实信号,现只吃画像判据),画像/
    生成/物化任一环节出错都不应挡住开单本身(义务清单是供料层,不是开单主路径的一部分)。
    """
    try:
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        if profile is None:
            return
        defs = tax_profile_store.load_active_defs(cur)
        obligations = obligation_engine.generate_obligations(
            profile=profile, period=period, data_signals=None, defs=defs
        )
        obligation_engine.materialize_obligations(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            work_order_id=work_order_id,
            period=period,
            obligations=obligations,
        )
    except Exception:
        logger.exception("obligation_engine generation failed on open_order (tenant=%s)", tenant_id)


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
        "kind": payload.get("kind"),  # 方向裁决(assign_kind)携带的裁定 kind,普通裁决为 None
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
    kind: Optional[str] = None,
    reason: Optional[str] = None,
) -> dict:
    """落人工裁决事件(CLI --decide 同语义)。金额裁决(face_value/recalc/exclude)带 values;
    方向裁决(assign_kind)带 kind;豁免(waive)带 reason(必填)。校验裁决合法 + item 确属
    该单,否则拒。"""
    payload = _decision_payload(item_id, decision, values, kind, reason)
    item = store.get_item(cur, tenant_id=tenant_id, work_order_id=work_order_id, item_id=item_id)
    if not item:
        raise WorkOrderApiError("workorder.item_not_found")
    return store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=_DECISION_STEP,
        event_type=_EVT_DECISION,
        payload=payload,
        actor=actor,
    )


def _decision_payload(
    item_id: str, decision: str, values: Optional[dict], kind: Optional[str], reason: Optional[str]
):
    """裁决事件 payload 构造 + 合法性校验。方向裁决的 kind 必须在允许集内;豁免的 reason 必填。"""
    if decision == decisions.ASSIGN_KIND:
        if kind not in decisions.ASSIGN_KINDS:
            raise WorkOrderApiError("workorder.decision_invalid")
        return {"item_id": item_id, "decision": decision, "kind": kind}
    if decision == decisions.WAIVE:
        reason_s = (reason or "").strip()
        if not reason_s:
            raise WorkOrderApiError("workorder.waive_reason_required")
        if len(reason_s) > _MAX_NOTE_LEN:
            raise WorkOrderApiError("workorder.waive_reason_too_long")
        return {"item_id": item_id, "decision": decision, "reason": reason_s}
    if decision in _DECISIONS:
        return {"item_id": item_id, "decision": decision, "values": values or {}}
    raise WorkOrderApiError("workorder.decision_invalid")


def _valid_amount(raw) -> str:
    """销项金额校验:十进制字符串、有限、非负。返回规范化字符串(全程 str/Decimal,禁 float)。
    去千分位后交 Decimal,解不出/负数/非有限一律拒。"""
    if raw is None:
        raise WorkOrderApiError("workorder.sales_summary_invalid")
    s = str(raw).strip().replace(",", "")
    if not s:
        raise WorkOrderApiError("workorder.sales_summary_invalid")
    try:
        value = Decimal(s)
    except InvalidOperation as exc:
        raise WorkOrderApiError("workorder.sales_summary_invalid") from exc
    if not value.is_finite() or value < 0:
        raise WorkOrderApiError("workorder.sales_summary_invalid")
    return format(value, "f")


def record_sales_summary(
    cur,
    *,
    tenant_id: str,
    work_order_id: str,
    sales_amount,
    output_vat,
    note: Optional[str],
    actor: str,
) -> dict:
    """人工填销项:销售额/销项税落成与 classify 直读同构的 item_classified(sales_summary,
    status=ok)事件,sales_read 载荷带单行合成表 —— reconcile 的 R2 回放据此解锁,引擎/steps
    不动一行。凭据备注随载荷留底(状态诚实:交付包据此标注「来源=人工申报」,不与直读混淆)。

    幂等:同工单只保留一条人工销项件(固定 dedupe_key,重填复用同一 item),重填以最新事件
    为准——reconcile 回放 latest-wins,旧值自然被覆盖,不会重复计入。"""
    sales_s = _valid_amount(sales_amount)
    vat_s = _valid_amount(output_vat)
    note_s = (note or "").strip()
    if len(note_s) > _MAX_NOTE_LEN:
        raise WorkOrderApiError("workorder.sales_summary_note_too_long")

    item = store.add_item(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        source=_MANUAL_SOURCE,
        kind=_SALES_KIND,
        status="ok",
        dedupe_key=_MANUAL_SALES_DEDUPE,
    )
    sales_read = {
        "headers": [_SALES_HEADER, _OUTPUT_VAT_HEADER],
        "rows": [{"cells": [sales_s, vat_s], "is_summary": False}],
        "source": "manual_entry",
        "note": note_s,
    }
    return store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step="classify",
        event_type=_EVT_CLASSIFIED,
        payload={
            "item_id": item["id"],
            "kind": _SALES_KIND,
            "status": "ok",
            "sales_read": sales_read,
        },
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
