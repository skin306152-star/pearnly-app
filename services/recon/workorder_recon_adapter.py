# -*- coding: utf-8 -*-
"""工单事件流 → 银行对账候选票适配器(批次 E1)。

打分引擎 bank_recon_scoring.match_one_tx 期望的候选是「发票候选字段」
(amount/date/vendor/invoice_no/direction),历史上从 ocr_history 取(v1
run_matching_for_session)。本模块新增第二条数据接缝:候选票改从**工单事件流**
(item_classified 回放)取,让工单 reconcile 步能对着自己收进来的票据做逐笔对平。

职责边界:
  - 打分引擎一行不改——本模块只把事件流的票映射成它已经能吃的候选字典。
  - 纯函数、零副作用:输入是已查出的事件列表 + 已解析的银行流水行,输出是判定结果。
    不碰 DB、不碰 feature flag(闸判定在 reconcile.py 编排层),便于脱库单测。
  - 交付两张清单(方案拍板 5):缺票(有流水无票)/ 未达(有票无流水)。金额合计走
    Decimal(票面/流水原值字符串精确求和),不用 float——float 只存在于打分引擎内部
    的相似度计算,不参与钱的清算。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from services.recon.bank_recon_scoring import THRESH_AUTO, THRESH_SUGGEST, match_one_tx

_EVT_CLASSIFIED = "item_classified"
_EVT_DECISION = "human_decision"
_KIND_PURCHASE = "purchase_invoice"
_KIND_SALES_DOC = "sales_doc"
_KIND_NON_TAX = "non_tax"
_DECISION_ASSIGN = "assign_kind"

# 银行流水方向 → 候选类目倾向。score_direction 只认 category_tag 里的销售/费用词根:
# 付款(withdrawal/OUT)对应采购/费用票、收款(deposit/IN)对应销售/收入票。
_CAT_PURCHASE = "purchase"
_CAT_SALES = "sales"

_ZERO = Decimal("0")


def _dec(value: Any) -> Decimal:
    """金额字符串 → Decimal(去千分位);空/解不出 → 0。清算合计的单一转换口。"""
    if value is None:
        return _ZERO
    try:
        s = str(value).replace(",", "").strip()
        return Decimal(s) if s else _ZERO
    except InvalidOperation:
        return _ZERO


def _replay_latest(events: list[dict], event_type: str) -> dict[str, dict]:
    """回放某类事件到 {item_id: payload},同 item 多条后者胜(反映最新识别/裁决)。"""
    out: dict[str, dict] = {}
    for e in events:
        if e.get("event_type") != event_type:
            continue
        payload = e.get("payload") or {}
        item_id = payload.get("item_id")
        if item_id:
            out[item_id] = payload
    return out


def _effective_kind(classified: dict, decision: Optional[dict]) -> Optional[str]:
    """票的有效类别:人工方向裁决(assign_kind)优先于 OCR 归堆的 kind。

    无裁决 → 用 classified kind(方向不明票 kind=unknown,类目留空 → 方向中性打分)。
    """
    if decision and decision.get("decision") == _DECISION_ASSIGN and decision.get("kind"):
        return decision["kind"]
    return classified.get("kind")


def _category_tag(kind: Optional[str]) -> str:
    """有效类别 → 打分引擎认的类目词(采购/销售/中性)。"""
    if kind == _KIND_PURCHASE:
        return _CAT_PURCHASE
    if kind == _KIND_SALES_DOC:
        return _CAT_SALES
    return ""


def candidates_from_events(events: list[dict]) -> list[dict]:
    """工单事件流(item_classified 回放)→ 打分引擎候选票列表。

    只收带票面 money 的票(进项票 + 方向不明票——两者 classify 都快照了钱字段);
    non_tax 裁决的票排除(已判无税务要素,不该进对账)。字段映射:
      total_amount → amount_total(打分引擎金额位;引擎侧自带 amount_total or total 兜底)
      invoice_date → invoice_date(日期位;classify 由 OCR date 快照,缺则日期分为 0)
      seller_name  → vendor(关键词位,软加分)
      invoice_number → invoice_no
      有效类别     → category_tag(方向位)
    """
    classified = _replay_latest(events, _EVT_CLASSIFIED)
    decisions = _replay_latest(events, _EVT_DECISION)
    out: list[dict] = []
    for item_id, payload in classified.items():
        money = payload.get("money")
        if not money:
            continue
        kind = _effective_kind(payload, decisions.get(item_id))
        if kind == _KIND_NON_TAX:
            continue
        out.append(
            {
                "id": item_id,
                "amount_total": money.get("total_amount"),
                "invoice_date": money.get("invoice_date"),
                "vendor": money.get("vendor"),
                "invoice_no": money.get("invoice_number"),
                "category_tag": _category_tag(kind),
            }
        )
    return out


def _tx_dict(
    deposit: Decimal, withdrawal: Decimal, tx_date: Optional[str], description: str
) -> dict:
    """银行流水行的统一打分字典。方向按存/取哪侧有动定(deposit↔IN、withdrawal↔OUT),
    金额取动的那一侧绝对值;两侧都 0 的行(纯 B/F)金额为 0,不命中任何候选。
    `_amount` 留 Decimal 供清算,`amount` 是打分引擎的金额位(float)。"""
    direction = "IN" if deposit > withdrawal else "OUT"
    amount = deposit if direction == "IN" else withdrawal
    return {
        "amount": float(amount),
        "tx_date": tx_date,
        "direction": direction,
        "description": description or "",
        "_amount": amount,
    }


def tx_from_statement_row(row: Any) -> dict:
    """StatementRow(dataclass)→ 打分引擎期望的银行流水字典(bank_recon_types 的方向约定)。"""
    d = getattr(row, "date", None)
    tx_date = d.isoformat() if hasattr(d, "isoformat") else (str(d) if d else None)
    return _tx_dict(
        _dec(getattr(row, "deposit", 0)),
        _dec(getattr(row, "withdrawal", 0)),
        tx_date,
        getattr(row, "description", "") or "",
    )


def tx_from_gt_entry(entry: dict) -> dict:
    """金标语料(vision_ablation_v2/bank ground_truth)的 entry → 银行流水字典。

    语料每条带 deposit/withdrawal/transaction_date/description(见 bank_kbank_01.json),
    直接映射,供对账金标测试复用同一条打分路径。
    """
    return _tx_dict(
        _dec(entry.get("deposit")),
        _dec(entry.get("withdrawal")),
        entry.get("transaction_date"),
        entry.get("description") or "",
    )


@dataclass
class ReconResult:
    """一次工单流水↔票据对平的结果(佐证层,进 R3 gate + 证据链,不阻断出包)。

    auto_matched : 唯一高分(≥THRESH_AUTO)自动匹配对。
    review       : 多候选(THRESH_SUGGEST~THRESH_AUTO)待人审。
    missing_invoice : 缺票清单——有流水无票(无候选达 THRESH_SUGGEST 的流水)。
    unmatched_invoice : 未达清单——有票无流水(从未被任何流水匹配上的候选票)。
    diff         : 两张清单的金额合计 + 净差(Decimal 字符串,精确清算)。
    """

    auto_matched: list[dict] = field(default_factory=list)
    review: list[dict] = field(default_factory=list)
    missing_invoice: list[dict] = field(default_factory=list)
    unmatched_invoice: list[dict] = field(default_factory=list)
    diff: dict = field(default_factory=dict)

    def as_gate_payload(self) -> dict:
        """R3 gate / 证据链落库形态(纯可 JSON 序列化 dict)。"""
        return {
            "auto_matched_count": len(self.auto_matched),
            "review_count": len(self.review),
            "missing_invoice_count": len(self.missing_invoice),
            "unmatched_invoice_count": len(self.unmatched_invoice),
            "auto_matched": self.auto_matched,
            "review": self.review,
            "missing_invoice": self.missing_invoice,
            "unmatched_invoice": self.unmatched_invoice,
            "diff": self.diff,
        }


def reconcile_workorder(
    statement_txs: list[dict],
    candidates: list[dict],
    *,
    thresh_auto: int = THRESH_AUTO,
    thresh_suggest: int = THRESH_SUGGEST,
) -> ReconResult:
    """逐笔真对平:每条流水在候选票里打分,分桶为自动匹配 / 人审 / 缺票,尾部结算未达票。

    唯一高分(top1 ≥ thresh_auto 且严格高于第二名或独一份)→ 自动匹配;top1 落
    [thresh_suggest, thresh_auto) → 进人审(带 top5 候选);无候选达 thresh_suggest → 缺票。
    被自动匹配或进过人审的候选,视为「有对应流水」;剩下的候选 = 未达清单。
    """
    result = ReconResult()
    touched_candidate_ids: set[str] = set()
    missing_total = _ZERO

    for tx in statement_txs:
        scored = match_one_tx(tx, candidates)
        top = scored[0] if scored else None
        if top and top["score"] >= thresh_auto and _is_unique_top(scored, thresh_auto):
            touched_candidate_ids.add(top["history_id"])
            result.auto_matched.append(
                {
                    "tx": _tx_view(tx),
                    "candidate_id": top["history_id"],
                    "score": top["score"],
                    "reason": top["reason"],
                }
            )
        elif top and top["score"] >= thresh_suggest:
            qualifying = [s for s in scored if s["score"] >= thresh_suggest]
            for s in qualifying:
                touched_candidate_ids.add(s["history_id"])
            result.review.append(
                {
                    "tx": _tx_view(tx),
                    "candidates": [
                        {
                            "candidate_id": s["history_id"],
                            "score": s["score"],
                            "reason": s["reason"],
                        }
                        for s in qualifying
                    ],
                }
            )
        else:
            amt = tx.get("_amount", _dec(tx.get("amount")))
            missing_total += amt
            result.missing_invoice.append(_tx_view(tx))

    unmatched_total = _ZERO
    for cand in candidates:
        if cand["id"] in touched_candidate_ids:
            continue
        amt = _dec(cand.get("amount_total"))
        unmatched_total += amt
        result.unmatched_invoice.append(
            {
                "candidate_id": cand["id"],
                "amount": _fmt(amt),
                "invoice_no": cand.get("invoice_no"),
                "vendor": cand.get("vendor"),
            }
        )

    result.diff = {
        "missing_invoice_total": _fmt(missing_total),
        "unmatched_invoice_total": _fmt(unmatched_total),
        "net": _fmt(missing_total - unmatched_total),
    }
    return result


def _is_unique_top(scored: list[dict], thresh_auto: int) -> bool:
    """自动匹配只在 top1 是唯一到达自动档时成立——两张候选都 ≥85 时不自动定,交人审避免误配。"""
    high = [s for s in scored if s["score"] >= thresh_auto]
    return len(high) == 1


def _tx_view(tx: dict) -> dict:
    """流水对外视图(去掉内部 _amount 私有键,金额以字符串精确呈现)。"""
    amt = tx.get("_amount", _dec(tx.get("amount")))
    return {
        "amount": _fmt(amt),
        "tx_date": tx.get("tx_date"),
        "direction": tx.get("direction"),
        "description": tx.get("description"),
    }


def _fmt(value: Decimal) -> str:
    """Decimal → 定点字符串(不带科学计数)。"""
    return format(value, "f")
