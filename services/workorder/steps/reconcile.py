# -*- coding: utf-8 -*-
"""reconcile 步:勾稽四道闸(任务包 §5 步 4)。

纯编排:从事件流回放票面金额/人工裁决 → 调 reconcile_gates 的纯算法 → 按 R1→R2→R3→R4
顺序返回首个卡点或全绿。取数一律走事件流(item_classified 落的钱字段 / human_decision 裁决),
事件流既是证据链底座又是断点续跑恢复源——续跑时 classify 已跳过、ctx.data 为空,金额仍能从
事件回放,数字与一次跑完全一致。销项直读兼收 ctx.data 兜底(同进程单跑的 T4 契约)。

四道闸语义:
  R1 进项税=Σ票面   flagged 无裁决 → stuck(点名每张票),绝不默认吞进合计。
  R2 销项合计=POS直读 无可用直读源 → needs(["sales_summary"])。
  R3 银行           缺流水记备忘不 stuck;有流水时闸 pearnly_ai_bank_recon 开则逐笔真对平
                    (缺票/未达两清单进证据链,佐证层绝不阻断 package),闸关维持只判材料就绪。
  R4 试算平衡        进销派生内部分录,Σ借≠Σ贷(容差 0.01)→ stuck。纯函数,不落库、不碰
                    accounting 模块开关、不写任何真租户数据(真复式引擎接线留 M1)。
"""

from __future__ import annotations

from pathlib import Path

from core import feature_flags
from services.workorder import decisions
from services.workorder.engine import StepContext, StepResult
from services.workorder.steps import reconcile_gates as gates

_EVT_CLASSIFIED = "item_classified"
_EVT_DECISION = "human_decision"
_PURCHASE = "purchase_invoice"
_SALES = "sales_summary"
_BANK = "bank_statement"


def run(ctx: StepContext) -> StepResult:
    items = ctx.store.list_items(ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id)
    events = ctx.store.list_events(
        ctx.cur, tenant_id=ctx.tenant_id, work_order_id=ctx.work_order_id
    )
    classified = _replay_money(events)
    decisions_by_item = _replay(events, _EVT_DECISION)

    # R1 进项税。除已归堆的进项票外,还收编「方向不明」票:它们钱已 OCR 出来,只是进/销没判准,
    # 必须靠人工 assign_kind 裁决归位(裁进项才入 Σ),无裁决 → 与「flagged 无裁决」同等停机点名。
    purchases = [
        it for it in items if it["kind"] == _PURCHASE and it["status"] in ("ok", "flagged")
    ]
    ambiguous = [
        it
        for it in items
        if it["status"] == "flagged"
        and str(it.get("flag_reason") or "").startswith(decisions.DIRECTION_PREFIXES)
    ]
    r1 = gates.resolve_input_vat(purchases, classified, decisions_by_item, ambiguous=ambiguous)
    if r1["unresolved"]:
        return StepResult.stuck(r1["unresolved"])

    # R2 销项合计
    reads = _replay_sales_reads(events) or dict(ctx.data.get("sales_summary_reads") or {})
    if not reads:
        return StepResult.needs(["sales_summary"])
    r2 = gates.aggregate_sales(reads)
    if not r2["used"]:
        return StepResult.needs(["sales_summary"])

    # R3 银行材料存在性 + 逐笔真对平(pearnly_ai_bank_recon 闸)。闸关:逐字节维持存在性判定
    # 现状(only present/count/note)。闸开且有 bank_statement 件:把流水与工单事件流的票据
    # 逐笔打分对平,缺票/未达两张清单挂进 gate + 证据链(经 step_done 落库),绝不 stuck、绝不
    # 阻断 package——银行对账是佐证层,税额来自 R1/R2 不来自它。
    banks = [it for it in items if it["kind"] == _BANK]
    r3 = {"bank_statement_present": bool(banks), "bank_statement_count": len(banks)}
    if not banks:
        r3["note"] = "bank_statement_missing"
    elif _bank_recon_enabled(ctx):
        recon = _run_bank_recon(ctx, banks, events)
        if recon is not None:
            r3["recon"] = recon

    # R4 试算平衡(纯函数)
    tb = gates.trial_balance(r1["entries"], r2["sales_amount"], r2["output_vat"])
    if not tb["balanced"]:
        return StepResult.stuck(
            [f"trial_balance_unbalanced: 借={tb['debit']} 贷={tb['credit']} 差={tb['diff']}"]
        )

    purchase_amount = sum((e["net"] for e in r1["entries"]), gates.ZERO)
    result_gates = {
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
    }
    # R5 影子底稿(pearnly_ai_shadow_draft 闸)。闸关:_run_shadow_draft 返 None,gates 逐字节维持
    # 现状(无 r5_shadow 键)。闸开:把 R1 已裁分录 + R2 聚合销项过纯函数复式引擎产出三件套影子
    # 底稿,佐证层挂 r5_shadow——绝不 stuck、绝不阻断 package(影子只算不落法定表)。
    shadow = _run_shadow_draft(ctx, r1, r2)
    if shadow is not None:
        result_gates["r5_shadow"] = shadow

    return StepResult.ok(
        input_vat_total=str(r1["total"]),
        purchase_amount_total=str(purchase_amount),
        sales_amount_total=str(r2["sales_amount"]),
        output_vat_total=str(r2["output_vat"]),
        gates=result_gates,
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


def _run_bank_recon(ctx: StepContext, banks: list[dict], events: list[dict]) -> dict | None:
    """闸开时的 R3 逐笔对平:银行流水行(注入解析)+ 工单事件流候选票 → 缺票/未达两张清单。

    对平结果作为纯 dict 挂在 r3["recon"],随 reconcile 的 StepResult.ok 经 step_done 落进证据链
    (E2 人审界面据此读)。任何异常都收进 note 不上抛——佐证层绝不拖垮出包。
    """
    from services.recon import workorder_recon_adapter as adapter

    try:
        rows = _bank_statement_rows(ctx, banks)
        statement_txs = [adapter.tx_from_statement_row(r) for r in rows]
        candidates = adapter.candidates_from_events(events)
        result = adapter.reconcile_workorder(statement_txs, candidates)
        return result.as_gate_payload()
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "bank_recon_skipped"}


def _run_shadow_draft(ctx: StepContext, r1: dict, r2: dict) -> dict | None:
    """闸开时的 R5 影子底稿:已裁进项分录(r1["entries"] · {net,vat,grand})+ 聚合销项 →
    纯函数复式规则引擎 → 建议分录/科目余额/试算平衡。闸关返 None(gates 无 r5_shadow 键)。

    结果作为纯 dict 挂 r5_shadow,随 reconcile 的 StepResult.ok 经 step_done 落进证据链(F3 视图 /
    package 交付物据此渲染)。任何异常都收进 note 不上抛——佐证层绝不拖垮出包。
    """
    if not _shadow_draft_enabled(ctx):
        return None
    from services.accounting import workorder_shadow_adapter as adapter

    try:
        result = adapter.build_shadow(
            purchase_entries=r1["entries"],
            sales_amount=r2["sales_amount"],
            output_vat=r2["output_vat"],
        )
        return result.as_gate_payload()
    except Exception as exc:  # noqa: BLE001 - 佐证层单点隔离,绝不阻断 package
        return {"error": f"{type(exc).__name__}", "note": "shadow_draft_skipped"}


def _default_shadow_draft_enabled(ctx: StepContext) -> bool:
    """R5 影子底稿放量闸(pearnly_ai_shadow_draft)。按 tenant 判定;fail-closed 在 feature_flags 内部
    (基建抖动绝不误开影子路)。"""
    return feature_flags.pearnly_ai_shadow_draft_enabled_for(ctx.tenant_id)


def _default_bank_recon_enabled(ctx: StepContext) -> bool:
    """R3 真对平放量闸(pearnly_ai_bank_recon)。工单线只有 tenant_id,按 tenant 判定;
    fail-closed 在 feature_flags 内部(基建抖动绝不误开真对平路)。"""
    return feature_flags.pearnly_ai_bank_recon_enabled_for(ctx.tenant_id)


def _default_bank_statement_rows(ctx: StepContext, banks: list[dict]) -> list:
    """默认银行流水解析:逐件读 file_ref 字节 → 生产 bank_recon 解析器 → StatementRow 列表。

    单测全部注入替身(reconcile._bank_statement_rows = fake),本函数不在测试里跑 → 不触真解析
    /付费。解析失败的件跳过(佐证层不因单件坏料中断);多件流水行顺序拼接。
    """
    from services.recon.bank_recon_v2 import _parse_bank_statement_impl

    rows: list = []
    for it in banks:
        file_ref = it.get("file_ref")
        if not file_ref:
            continue
        data = Path(file_ref).read_bytes()
        parsed = _parse_bank_statement_impl(data, Path(file_ref).name, tenant_id=ctx.tenant_id)
        if parsed.get("ok"):
            rows.extend(parsed.get("rows") or [])
    return rows


# 注入点:模块级绑定,测试用 reconcile._xxx = fake 替换,不改调用方代码(同 classify 惯例)。
_bank_recon_enabled = _default_bank_recon_enabled
_bank_statement_rows = _default_bank_statement_rows
_shadow_draft_enabled = _default_shadow_draft_enabled
