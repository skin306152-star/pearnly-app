# -*- coding: utf-8 -*-
"""reconcile 步:勾稽四道闸(任务包 §5 步 4)。

纯编排:从事件流回放票面金额/人工裁决 → 调 reconcile_gates 的纯算法 → 按 R1→R2→R3→R4
顺序返回首个卡点或全绿。取数一律走事件流(item_classified 落的钱字段 / human_decision 裁决),
事件流既是证据链底座又是断点续跑恢复源——续跑时 classify 已跳过、ctx.data 为空,金额仍能从
事件回放,数字与一次跑完全一致。销项直读兼收 ctx.data 兜底(同进程单跑的 T4 契约)。

四道闸语义:
  R1 进项税=Σ票面   flagged 无裁决 → stuck(点名每张票),绝不默认吞进合计。
  R2 销项合计=POS直读 无可用直读源 → needs(["sales_summary"])。
  R3 银行           M0 只判材料就绪(有 bank_statement 件即就绪),缺则记备忘不 stuck。
  R4 试算平衡        进销派生内部分录,Σ借≠Σ贷(容差 0.01)→ stuck。纯函数,不落库、不碰
                    accounting 模块开关、不写任何真租户数据(真复式引擎接线留 M1)。
"""

from __future__ import annotations

from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import reconcile_gates as gates

_EVT_CLASSIFIED = "item_classified"
_EVT_DECISION = "human_decision"
_PURCHASE = "purchase_invoice"
_SALES = "sales_summary"
_BANK = "bank_statement"
# classify 判不出进/销方向的票落 kind=unknown + flag_reason 以下列前缀起头(sort.bin_ocr_fields):
#   direction_ambiguous       税号/名称锚点都对不上,进/销全然不明。
#   sales_direction_unhandled 自家==卖方,疑似本方销项票(M0 不自动归堆单张销项)。
# 两者都必须走人工方向裁决(assign_kind),不许被 R1 静默漏掉——G1/G1R2 黑洞的根因。
_DIRECTION_PREFIXES = ("direction_ambiguous", "sales_direction_unhandled")


def run(ctx: StepContext) -> StepResult:
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    classified = _replay_money(events)
    decisions = _replay(events, _EVT_DECISION)

    # R1 进项税。除已归堆的进项票外,还收编「方向不明」票:它们钱已 OCR 出来,只是进/销没判准,
    # 必须靠人工 assign_kind 裁决归位(裁进项才入 Σ),无裁决 → 与「flagged 无裁决」同等停机点名。
    purchases = [
        it for it in items if it["kind"] == _PURCHASE and it["status"] in ("ok", "flagged")
    ]
    ambiguous = [
        it
        for it in items
        if it["status"] == "flagged"
        and str(it.get("flag_reason") or "").startswith(_DIRECTION_PREFIXES)
    ]
    r1 = gates.resolve_input_vat(purchases, classified, decisions, ambiguous=ambiguous)
    if r1["unresolved"]:
        return StepResult.stuck(r1["unresolved"])

    # R2 销项合计
    reads = _replay_sales_reads(events) or dict(ctx.data.get("sales_summary_reads") or {})
    if not reads:
        return StepResult.needs(["sales_summary"])
    r2 = gates.aggregate_sales(reads)
    if not r2["used"]:
        return StepResult.needs(["sales_summary"])

    # R3 银行材料存在性(完整 GL↔银行对平是 M1)
    banks = [it for it in items if it["kind"] == _BANK]
    r3 = {"bank_statement_present": bool(banks), "bank_statement_count": len(banks)}
    if not banks:
        r3["note"] = "bank_statement_missing"

    # R4 试算平衡(纯函数)
    tb = gates.trial_balance(r1["entries"], r2["sales_amount"], r2["output_vat"])
    if not tb["balanced"]:
        return StepResult.stuck(
            [f"trial_balance_unbalanced: 借={tb['debit']} 贷={tb['credit']} 差={tb['diff']}"]
        )

    purchase_amount = sum((e["net"] for e in r1["entries"]), gates.ZERO)
    return StepResult.ok(
        input_vat_total=str(r1["total"]),
        purchase_amount_total=str(purchase_amount),
        sales_amount_total=str(r2["sales_amount"]),
        output_vat_total=str(r2["output_vat"]),
        gates={
            "r1_input_vat": {"total": str(r1["total"]), "counted": len(r1["entries"])},
            "r2_sales": {
                "sales_amount": str(r2["sales_amount"]),
                "output_vat": str(r2["output_vat"]),
            },
            "r3_bank": r3,
            "r4_trial_balance": {
                "balanced": True,
                "debit": str(tb["debit"]),
                "credit": str(tb["credit"]),
            },
        },
    )


def _replay(events: list[dict], event_type: str) -> dict:
    """回放某类事件到 {item_id: payload}(同 item 多条时后者胜,反映最新裁决/识别)。"""
    out: dict = {}
    for e in events:
        if e["event_type"] != event_type:
            continue
        payload = e.get("payload") or {}
        iid = payload.get("item_id")
        if iid:
            out[iid] = payload
    return out


def _replay_money(events: list[dict]) -> dict:
    """票面钱字段:任何带 money 载荷的 item_classified 事件(进项票 + 方向不明票——后者
    钱已读出,待人工定向后按裁定 kind 决定是否进 R1)。按 item_id 回放,latest-wins。"""
    out: dict = {}
    for p in _replay(events, _EVT_CLASSIFIED).values():
        if p.get("money"):
            out[p["item_id"]] = p["money"]
    return out


def _replay_sales_reads(events: list[dict]) -> dict:
    """销项直读:item_classified(kind=sales_summary)的 sales_read 载荷(续跑安全的主源)。"""
    out: dict = {}
    for p in _replay(events, _EVT_CLASSIFIED).values():
        if p.get("kind") == _SALES and p.get("sales_read"):
            out[p["item_id"]] = p["sales_read"]
    return out
