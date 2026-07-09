# -*- coding: utf-8 -*-
"""勾稽四道闸的纯计算核(reconcile.py 的算法层 · 任务包 §5 步 4)。

本文件零副作用、不碰 store/DB:输入是已从事件流回放好的普通字典,输出是金额与判定。
把「取数(reconcile.py)」和「算数(本文件)」分开,让四道闸的红/绿逻辑能脱离编排单独验证,
也把编排文件压到单一职责。钱一律 Decimal,容差 0.01;金额来源全部是票面/直读的原值,本层
只做求和与借贷派生,绝不重算业务金额(重算是 OCR/直读上游的事)。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

TOL = Decimal("0.01")
ZERO = Decimal("0")

# 汇总表列角色识别关键词(泰/英)。先认销项税列再认销售额列,避免销售额误命中税额列。
_SALES_HINTS = ("ยอดขาย", "มูลค่า", "จำนวนเงิน", "รวมเงิน", "sales", "amount", "ยอด")
_VAT_HINTS = ("ภาษีขาย", "ภาษีมูลค่า", "vat", "ภาษี", "tax")


def to_dec(v: Any) -> Decimal:
    """任意值 → Decimal,去千分位;空/解不出 → 0(不抛,金额缺失由上层判 unresolved)。"""
    if v is None:
        return ZERO
    try:
        s = str(v).replace(",", "").strip()
        return Decimal(s) if s else ZERO
    except InvalidOperation:
        return ZERO


def _effective(money: dict) -> dict:
    """票面派生分录金额:净额/税额取原值,含税额缺失时用 净+税 兜底(保证借贷自洽)。"""
    net = to_dec(money.get("subtotal"))
    vat = to_dec(money.get("vat"))
    grand = to_dec(money.get("total_amount"))
    if grand == ZERO:
        grand = net + vat
    return {"net": net, "vat": vat, "grand": grand}


def _recalc(money: dict, values: dict) -> dict:
    """人工「按重算」裁决:税额以裁决值为准,净额沿用票面,含税额派生成 净+税(恢复自洽)。"""
    net = to_dec(values.get("net")) or to_dec(money.get("subtotal"))
    vat = to_dec(values.get("vat"))
    grand = to_dec(values.get("grand_total")) or (net + vat)
    return {"net": net, "vat": vat, "grand": grand}


def _label(item: dict, money: dict) -> str:
    name = Path(item.get("file_ref") or "").name or item.get("id") or "?"
    inv = (money or {}).get("invoice_number")
    return f"{name}({inv})" if inv else name


def resolve_input_vat(purchases: list[dict], classified: dict, decisions: dict) -> dict:
    """R1:进项税 = Σ票面。ok 直接进;flagged 必须有人工裁决,否则计入 unresolved(绝不默认吞)。

    返回 {total, unresolved[], entries[]}。unresolved 非空 → 上层整步 stuck;entries 是被计入
    合计的派生分录金额(供 R4 试算)。缺 item_classified 金额事件的 ok/face_value 件也算 unresolved
    ——续跑丢事件时宁可停,不静默少算。
    """
    total = ZERO
    unresolved: list[str] = []
    entries: list[dict] = []
    for it in purchases:
        money = classified.get(it["id"]) or {}
        if it["status"] == "ok":
            if not money:
                unresolved.append(f"{_label(it, money)}: 缺 item_classified 金额事件")
                continue
            eff = _effective(money)
        else:  # flagged:查人工裁决
            dec = decisions.get(it["id"])
            if not dec:
                unresolved.append(
                    f"{_label(it, money)}: flagged({it.get('flag_reason')}) 无人工裁决"
                )
                continue
            eff = _apply_decision(it, money, dec, unresolved)
            if eff is None:
                continue
        total += eff["vat"]
        entries.append(eff)
    return {"total": total, "unresolved": unresolved, "entries": entries}


def _apply_decision(it: dict, money: dict, dec: dict, unresolved: list) -> Optional[dict]:
    """一张 flagged 票的裁决取数。exclude → 剔除(返回 None);未知裁决/缺料 → 计 unresolved。"""
    decision = dec.get("decision")
    if decision == "exclude":
        return None
    if decision == "face_value":
        if not money:
            unresolved.append(f"{_label(it, money)}: 按票面裁决但缺金额事件")
            return None
        return _effective(money)
    if decision == "recalc":
        values = dec.get("values") or {}
        if not values.get("vat"):
            unresolved.append(f"{_label(it, money)}: 按重算裁决但未给 vat")
            return None
        return _recalc(money, values)
    unresolved.append(f"{_label(it, money)}: 未知裁决 {decision!r}")
    return None


def _first_match(headers_lower: list[str], hints: tuple, exclude: Optional[int]) -> Optional[int]:
    for i, h in enumerate(headers_lower):
        if i == exclude:
            continue
        if any(hint in h for hint in hints):
            return i
    return None


def _detect_cols(headers: list) -> tuple[Optional[int], Optional[int]]:
    """从表头认「销售额列」「销项税列」下标。先认税列,销售额列再排除税列避免撞列。"""
    lower = [str(h).strip().lower() for h in headers]
    vat_idx = _first_match(lower, _VAT_HINTS, exclude=None)
    sales_idx = _first_match(lower, _SALES_HINTS, exclude=vat_idx)
    return sales_idx, vat_idx


def _cell_num(cells: list, idx: Optional[int]) -> Decimal:
    if idx is None or idx >= len(cells):
        return ZERO
    return to_dec(cells[idx])


def aggregate_sales(reads: dict) -> dict:
    """R2:POS 直读聚合销售额/销项税。按表头认列,逐行求和,跳过底部合计行(不重复计)。

    返回 {sales_amount, output_vat, used}。used=False 表示所有直读都认不出销售额列(无法产出销项
    合计),上层据此判 needs——诚实反映缺可用直读源,不硬造数字。
    """
    sales_total = ZERO
    vat_total = ZERO
    used = False
    for parsed in reads.values():
        s_idx, v_idx = _detect_cols(parsed.get("headers") or [])
        if s_idx is None:
            continue
        used = True
        for r in parsed.get("rows") or []:
            if r.get("is_summary"):
                continue
            cells = r.get("cells") or []
            sales_total += _cell_num(cells, s_idx)
            vat_total += _cell_num(cells, v_idx)
    return {"sales_amount": sales_total, "output_vat": vat_total, "used": used}


def trial_balance(purchase_entries: list[dict], sales_amount: Decimal, output_vat: Decimal) -> dict:
    """R4:纯函数试算平衡。进项 借[净+税]贷[含税];销项 借[含税]贷[净+税]。Σ借=Σ贷 即平。

    销项两侧恒等自平;不平只可能来自某张进项票 含税≠净+税(票面自身对不上,classify 的
    净×7% 闸抓不到这一等式)——即 M0 试算真正拦的是这类票面内部不自洽,非重算业务金额。
    """
    debit = ZERO
    credit = ZERO
    for e in purchase_entries:
        debit += e["net"] + e["vat"]
        credit += e["grand"]
    gross = sales_amount + output_vat
    debit += gross
    credit += gross
    diff = (debit - credit).copy_abs()
    return {"balanced": diff <= TOL, "debit": debit, "credit": credit, "diff": diff}
