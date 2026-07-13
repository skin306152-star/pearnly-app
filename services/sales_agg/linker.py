# -*- coding: utf-8 -*-
"""跨渠道关联:银行入账 ↔ EDC 结算(settlement_of)+ 税票/EDC 同日共存疑似点名。

同一笔卡销售会在三处留痕:EDC 结算单(毛额)、银行到账(净额,通常 T+1/T+2)、可能还开了
全额税票。销项只按 EDC 毛额计,银行到账必须被认出是「某张结算单的钱到了」并从销售侧摘除,
否则缺口探测会报虚缺;认不出的到账/结算单交聚合层进 gaps,不硬配。

v1 不自动判税票与 EDC 的重复(判错=直接错税额),同日共存只逐笔点名交会计在 SA-2 裁。
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable, Optional

from services.sales_agg.model import BankCredit, EdcSettlement, SalesDoc

# 结算到账通常 T+1/T+2(节假日顺延),窗口再宽就开始误配同额结算单。
DATE_WINDOW_DAYS = 2
TOL = Decimal("0.01")


def link_settlements(
    edc_rows: list[EdcSettlement], bank_rows: list[BankCredit]
) -> tuple[list[dict], list[dict], set[str], set[str]]:
    """一对一贪心匹配:日期差最小者先配;金额 ≈ 净额 或 ≈ 毛额−手续费(容差 0.01)。

    返回 (links, conflicts, matched_bank_refs, matched_edc_refs)。匹配成对后再做
    「到账+手续费≈毛额」交叉核对,不平点名进 conflicts(§4 命门)。
    """
    candidates = []
    for credit in bank_rows:
        if not credit.usable:
            continue
        for edc in edc_rows:
            if not edc.usable:
                continue
            diff = abs((credit.day - edc.day).days)
            if diff > DATE_WINDOW_DAYS:
                continue
            basis = _amount_basis(credit.amount, edc)
            if basis:
                candidates.append((diff, credit, edc, basis))
    # 排序键含双方 ref,同分候选的取舍确定(重跑逐字节一致)。
    candidates.sort(key=lambda c: (c[0], c[1].ref, c[2].ref))

    links: list[dict] = []
    conflicts: list[dict] = []
    matched_bank: set[str] = set()
    matched_edc: set[str] = set()
    for diff, credit, edc, basis in candidates:
        if credit.ref in matched_bank or edc.ref in matched_edc:
            continue
        matched_bank.add(credit.ref)
        matched_edc.add(edc.ref)
        links.append(
            {
                "kind": "settlement_of",
                "bank_ref": credit.ref,
                "edc_ref": edc.ref,
                "matched_on": basis,
                "date_diff_days": diff,
                "amount": str(credit.amount),
            }
        )
        imbalance = _crosscheck(credit, edc)
        if imbalance is not None:
            conflicts.append(
                {
                    "kind": "settlement_crosscheck_imbalance",
                    "refs": [credit.ref, edc.ref],
                    "detail": (
                        f"到账 {credit.amount} + 手续费 {edc.fee} ≠ 毛额 {edc.gross}"
                        f"(差 {imbalance})"
                    ),
                }
            )
    return links, conflicts, matched_bank, matched_edc


def edc_internal_conflicts(edc_rows: Iterable[EdcSettlement]) -> list[dict]:
    """结算单自身恒等式:毛额 − 手续费 = 净额。三数齐且不平 → 点名(单据读错或异常扣款)。"""
    out = []
    for edc in edc_rows:
        if edc.gross is None or edc.fee is None or edc.net is None or edc.gross_derived:
            continue
        delta = edc.gross - edc.fee - edc.net
        if abs(delta) > TOL:
            out.append(
                {
                    "kind": "edc_internal_imbalance",
                    "refs": [edc.ref],
                    "detail": f"毛额 {edc.gross} − 手续费 {edc.fee} ≠ 净额 {edc.net}(差 {delta})",
                }
            )
    return out


def overlap_suspects(doc_rows: Iterable[SalesDoc], edc_days: set[date]) -> list[dict]:
    """税票与 EDC 同日共存 → 疑似同笔销售两处留痕,逐笔点名不自动判重(§4 定案)。"""
    out = []
    for doc in doc_rows:
        if doc.usable and doc.day in edc_days:
            out.append(
                {
                    "kind": "doc_edc_overlap_suspect",
                    "refs": [doc.ref],
                    "detail": (
                        f"{doc.day.isoformat()} 税票 {doc.invoice_no or doc.ref}"
                        f"({doc.gross})与当日 EDC 结算共存,可能是同笔卡销售,请人工核"
                    ),
                }
            )
    return out


def _amount_basis(amount: Decimal, edc: EdcSettlement) -> Optional[str]:
    if edc.net is not None and abs(amount - edc.net) <= TOL:
        return "net"
    if edc.fee is not None and abs(amount - (edc.gross - edc.fee)) <= TOL:
        return "gross_minus_fee"
    return None


def _crosscheck(credit: BankCredit, edc: EdcSettlement) -> Optional[Decimal]:
    """到账 + 手续费 ≈ 毛额(容差 0.01)。手续费缺失无从核,交叉核对不硬编。"""
    if edc.fee is None:
        return None
    delta = credit.amount + edc.fee - edc.gross
    return delta if abs(delta) > TOL else None
