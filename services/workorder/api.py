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

from core import feature_flags
from services.workorder import (
    decisions,
    evidence,
    kinds,
    obligation_engine,
    progress as wo_progress,
    sod,
    store,
    wht_signals,
)
from services.workorder.steps import bank_sales_suggest, edc_corroboration, sales_aggregate
from services.workspace import tax_profile_store

logger = logging.getLogger(__name__)

# 人工裁决三态,与 CLI --decide 同语义(见 L2-验收.md):
#   face_value=确认票面 OCR 读数 · recalc=人工看原票补正 · exclude=剔除不计入
_DECISIONS = (decisions.FACE_VALUE, decisions.RECALC, decisions.EXCLUDE)
_DECISION_STEP = "reconcile"
_EVT_DECISION = "human_decision"
_EVT_CLASSIFIED = "item_classified"
_EVT_BANK_PARSED = "item_bank_parsed"
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
_SALES_KIND = kinds.SALES_SUMMARY
_MANUAL_SOURCE = "manual"
_MANUAL_SALES_DEDUPE = "manual:sales_summary"
_MAX_NOTE_LEN = 500
_KIND_BANK_STATEMENT = kinds.BANK_STATEMENT
# reconcile.aggregate_sales 靠表头关键词认「销售额列 / 销项税列」;人工填的两个合计以泰文规范
# 列名 + 单数据行合成表落库,与真实 POS 汇总表直读产出的 sales_read 形状一致(不另造契约)。
_SALES_HEADER = "ยอดขาย"
_OUTPUT_VAT_HEADER = "ภาษีขาย"

# 复核签批(C3 · 四权分立)。review 态内 append-only 事件,不新增状态位。
_REVIEW_STEP = "review"
_EVT_REVIEW_SIGNOFF = "review_signoff"
_REVIEW_ROLE = "reviewer"


class WorkOrderApiError(ValueError):
    """业务级校验错(路由映射成 4xx)。code 给前端错误契约;context 带结构化补充(如冻结闸
    点名的缺失文件清单),路由原样透传给前端。"""

    def __init__(self, code: str, *, context: Optional[dict] = None):
        super().__init__(code)
        self.code = code
        self.context = context or {}


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
    if feature_flags.pearnly_ai_m1_enabled_for(tenant_id, None):
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
    """开单即生成一次当期义务清单(税务画像-方案-B1.md §3 · B2-d · D1-2)。当期采购 WHT
    真实信号由 wht_signals 扫出后喂给引擎(个人→PND3 / 法人→PND53 数据触发);画像读取/
    信号扫描/生成/物化任一环节出错都不挡开单本身(义务清单是供料层,不是开单主路径的一
    部分)——profile 读取本身也可能炸(DB 抖动),故这里单独兜底,不指望
    rematerialize_for_profile 的内部 try/except(它只包 defs→生成→物化三步,profile 是
    调用方职责)。信号扫描走独立只读连接(见 wht_signals.scan_period_wht_signals_isolated),
    绝不用本开单写游标——防交接债 #2 的「共享游标查询失败 abort 事务 → commit 静默丢工单」。
    """
    try:
        profile = tax_profile_store.get_profile(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
    except Exception:
        logger.exception(
            "obligation_engine profile fetch failed on open_order (tenant=%s)", tenant_id
        )
        return
    if profile is None:
        return
    data_signals = wht_signals.scan_period_wht_signals_isolated(
        tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    obligation_engine.rematerialize_for_profile(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        profile=profile,
        work_order_id=work_order_id,
        data_signals=data_signals,
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
    # item_classified 回放同一请求只算一次,喂给 flagged/进度/佐证三个读侧投影(纯参数下沉)。
    classified = evidence.replay_items_by_type(events, _EVT_CLASSIFIED)
    # item_bank_parsed 回放同上(J-B:reconcile 步银行流水逐件进度,同 classified 的现算范式)。
    bank_parsed = evidence.replay_items_by_type(events, _EVT_BANK_PARSED)
    detail = {
        "id": wo["id"],
        "workspace_client_id": wo["workspace_client_id"],
        "period": wo["period"],
        "intent": wo["intent"],
        "status": wo["status"],
        "current_step": wo["current_step"],
        "progress": wo_progress.classify_progress(wo, items, classified),
        "bank_progress": wo_progress.bank_progress(wo, items, bank_parsed),
        "flagged": evidence.flagged_projection(items, events, classified=classified),
        "alerts": evidence.alerts_projection(events) + evidence.amount_read_suggestions(events),
        "needs": needs,
        "blocked_reasons": blocked,
        "numbers": _numbers(events),
        "bank_recon": _bank_recon(events, items),
        "shadow_draft": shadow_draft(events),
        "financials": _financials(events),
        "sales_corroboration": sales_aggregate.corroboration_for_detail(
            events, items, classified=classified
        ),
        "edc_corroboration": edc_corroboration.corroboration_for_detail(
            events, classified=classified
        ),
        "deliverables": [
            {"kind": d["kind"], "numbers": d.get("numbers") or {}} for d in deliverables
        ],
    }
    # SA-3a 倒推销项建议:闸关则不挂键(order_detail 逐字节维持现状,现有人工填销项路径不变)。
    if feature_flags.pearnly_ai_bank_sales_suggest_enabled_for(tenant_id):
        detail["bank_sales_suggestion"] = bank_sales_suggest.suggest(events)
    return detail


def bank_recon_raw(events: list[dict]) -> Optional[dict]:
    """R3 银行对账清单原始 dict(reconcile 步 step_done 落库的 recon,未叠加 bank_item_ids /
    人审裁决覆盖)。闸关 / 无银行流水 / 尚未跑到 reconcile / 引擎异常降级都诚实给 None——
    recon 提取判定收口在 evidence.bank_recon_from_step_done(与 bank_recon_review 的窄读路
    共用单一事实源,见 record_bank_decision)。"""
    return evidence.bank_recon_from_step_done(evidence.replay_step_done(events, _DECISION_STEP))


def _bank_recon(events: list[dict], items: list[dict]) -> Optional[dict]:
    """R3 银行对账四清单只读投影(E2 对账人审界面读侧)。

    bank_item_ids 是本工单已收的银行流水件(kind=bank_statement),供前端「缺票行推
    LINE 待问」的落点与「查看原图」共用——缺票行本身没有对应票据 item,问题与原图都
    只能挂在流水件本身上(问的就是"这张流水缺哪张票")。review 清单逐笔叠加人审裁决
    (MC1-b3 · accept/reject,见 _overlay_bank_decisions)——只改呈现,不改 R1/R2/R4。"""
    recon = bank_recon_raw(events)
    if recon is None:
        return None
    bank_item_ids = [it["id"] for it in items if it.get("kind") == _KIND_BANK_STATEMENT]
    recon = dict(recon, bank_item_ids=bank_item_ids)
    return _overlay_bank_decisions(recon, events)


def _overlay_bank_decisions(recon: dict, events: list[dict]) -> dict:
    """review 清单逐笔叠加人审裁决(MC1-b3 · E2 债)。零副作用:不改 recon 入参,命中的
    review 条目换成带 human_decision 的新 dict;auto_matched/missing_invoice/unmatched_invoice
    三张清单与 diff 合计一字不动——银行对账四清单本身不回流 R1/R2 税额。"""
    decisions_by_tx = evidence.bank_recon_decisions(events)
    if not decisions_by_tx or not recon.get("review"):
        return recon
    review = []
    for entry in recon["review"]:
        tx_id = (entry.get("tx") or {}).get("statement_tx_id")
        dec = decisions_by_tx.get(tx_id) if tx_id else None
        review.append(dict(entry, human_decision=dec) if dec else entry)
    return dict(recon, review=review)


def _gate_projection(events: list[dict], *, gate_key: str, required_key: str) -> Optional[dict]:
    """从 reconcile 步 step_done 深取某佐证 gate 的只读投影:闸关(无该键)/ 尚未跑到 reconcile /
    引擎异常降级残影(缺 required_key)一律诚实给 None,不拼假数据充数(状态诚实优先于"看着有
    内容")。R5 影子底稿(shadow_draft)与 R6 报表(_financials)共用此深取范式,不各写一份。"""
    payload = evidence.replay_step_done(events, _DECISION_STEP)
    gate = (payload.get("gates") or {}).get(gate_key) if payload else None
    return gate if isinstance(gate, dict) and required_key in gate else None


def shadow_draft(events: list[dict]) -> Optional[dict]:
    """R5 影子底稿三件套只读投影(F3 影子底稿视图读侧 + M1-3KEY 键二分录导出)。深取
    gates.r5_shadow;降级残影缺 trial_balance → None(_run_shadow_draft 的 skipped 残影不充数)。"""
    return _gate_projection(events, gate_key="r5_shadow", required_key="trial_balance")


def _financials(events: list[dict]) -> Optional[dict]:
    """R6 月度报表三件套只读投影(G1b 报表包视图读侧)。深取 gates.r6_financials;闸关/影子跳过/
    降级残影缺 balance_sheet → None(_run_shadow_financials 的 skipped 残影不充数)。"""
    return _gate_projection(events, gate_key="r6_financials", required_key="balance_sheet")


def financials_projection(cur, *, tenant_id: str, work_order_id: str) -> Optional[dict]:
    """报表下载路由专用薄函数:只回放事件取 financials 投影,不算整份 order_detail
    (下载端点只消费这一个键,没必要连 flagged/银行对账/佐证全算一遍)。语义与
    order_detail()['financials'] 同一份 _financials,不另造第二套判定。"""
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    return _financials(events)


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


def record_review_signoff(
    cur, *, tenant_id: str, work_order_id: str, actor: str, note: Optional[str] = None
) -> dict:
    """复核签批(review 态内 append-only 事件,不新增状态)。SoD flag 开时复核人不得是
    制单人(services.workorder.sod.reviewer_violation);同一复核人重签幂等覆盖(dedupe_key
    含 actor,一人一条,latest-wins)。"""
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    violation = sod.reviewer_violation(
        events, actor, enforced=feature_flags.pearnly_ai_sod_enabled_for(tenant_id)
    )
    if violation:
        raise WorkOrderApiError(violation)
    note_s = (note or "").strip()
    if len(note_s) > _MAX_NOTE_LEN:
        raise WorkOrderApiError("workorder.review_note_too_long")
    return store.append_event(
        cur,
        tenant_id=tenant_id,
        work_order_id=work_order_id,
        step=_REVIEW_STEP,
        event_type=_EVT_REVIEW_SIGNOFF,
        payload={"role": _REVIEW_ROLE, "note": note_s},
        actor=actor,
        dedupe_key=f"review:{work_order_id}:{actor}",
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
