# -*- coding: utf-8 -*-
"""services/ocr/sanity.py · 发票合理性硬闸(确定性·绝不静默放过)。

triggers.py 决定「要不要再看一眼(L3 视觉复读)」,是软信号;本模块决定「这数压根
不可能对,别让它静默入账」,是硬信号 → 命中即强制转人工(needs_manual_review)。

根因(2026-06-29 vertex 切换实测复盘):
  · 自洽 ≠ 正确:BBL2645 的 −114万、pur05 的 44.67 内部都自洽,容差闸放过了它们。
  · 没有绝对合理性下限:期初负数、总额 < 单条明细,这类该直接拒。
  · 默认不诚实:校验不过仍静默 auto,而非转人工。

只在 document_type ∈ {tax_invoice, simplified_tax_invoice, receipt, credit_note, other}
的发票路调用(GL/银行走各自 validator)。纯函数:不连模型、不读 IO、duck-typed 取属性。

★诚实边界:本闸抓的是「结构上不可能」的错(负数/串税号/总额低于单行/缺VAT勾稽不平),
抓不住「语义选错列且无明细佐证」的 pur05-44.67 那类 —— 那需要供应商历史量级基线(另一道
闸,见 [[ocr-determinism-layer-root-cause]])。不在此夸大覆盖。
"""

from __future__ import annotations

import re
from typing import List, Optional

# 钱字段比对容差(泰铢):吸收四舍五入,又抓得住真错。
_TOL = 0.5
# 泰国标准 VAT 7%;缺 VAT 时用它反推「总额−小计」是否落在合理区间。
_VAT_RATE = 0.07
# 缺 VAT 勾稽:|总额−小计| 与「0」或「7%小计」的相对偏离超此比例才判不平(吸收分位四舍五入)。
_RECON_REL = 0.02


def _money(v) -> Optional[float]:
    """'1,780.00' / '฿1780' / 1780 → float;空/不可解 → None。"""
    if v is None:
        return None
    s = re.sub(r"[^\d.\-]", "", str(v).replace(",", "").strip())
    if not s or s in ("-", ".", "-."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _digits(v) -> str:
    return re.sub(r"\D", "", str(v or ""))


def _line_subtotals(invoice) -> List[float]:
    out: List[float] = []
    for it in getattr(invoice, "items", None) or []:
        amt = _money(getattr(it, "subtotal", None))
        if amt is not None and amt > 0:
            out.append(amt)
    return out


def evaluate_sanity(invoice) -> List[str]:
    """返回硬否决原因列表(空=通过)。命中任一 → 调用方强制转人工,绝不 auto。

    每条规则都保守:只在「结构上不可能对」时触发,宁可漏抓(交给软闸/人工)也不误杀
    正常票(误杀 = 凭空增加人工量 + 失去信任)。
    """
    if getattr(invoice, "is_not_invoice", False):
        return []

    reasons: List[str] = []
    sub = _money(getattr(invoice, "subtotal", None))
    vat = _money(getattr(invoice, "vat", None))
    total = _money(getattr(invoice, "total_amount", None))
    discount = _money(getattr(invoice, "discount", None))

    # 规则 1:负数金额。发票的小计/税额/总额不可能为负(贷项单 credit_note 例外:整单冲红)。
    is_credit_note = getattr(invoice, "document_type", "") == "credit_note"
    if not is_credit_note:
        for name, val in (("total_amount", total), ("subtotal", sub), ("vat", vat)):
            if val is not None and val < 0:
                reasons.append(f"{name} 为负数({val}) — 发票金额不可能为负")

    # 规则 2:卖方税号 == 买方税号。买方表头税号被串进卖方(inv01)→ 方向/抵扣全错。
    st, bt = _digits(getattr(invoice, "seller_tax", None)), _digits(
        getattr(invoice, "buyer_tax", None)
    )
    if st and bt and len(st) >= 10 and st == bt:
        reasons.append(f"卖方税号 == 买方税号({st}) — 大概率串了表头税号")

    # 规则 3:总额 < 最大单行小计(且无折扣)。总额至少 ≥ 任一单行;低于即选错列(pur05 类,
    # 仅当明细在场)。有折扣时总额可能合法地低于单行 → 跳过不误杀。
    lines = _line_subtotals(invoice)
    if total is not None and total > 0 and lines and not (discount and discount > 0):
        biggest = max(lines)
        if total < biggest - _TOL:
            reasons.append(f"总额 {total} < 单条明细 {biggest} — 不可能(疑选错列)")

    # 规则 4(洞④ · triggers.py:85 的盲区):缺 VAT 但小计与总额都在且对不上。
    # 现有数学闸三字段缺一就跳过 → VAT 缺时静默放行。这里补勾稽:净额 = 小计 − 折扣
    # (泰国 VAT 基数在折扣后),总额必须 ≈ 净额(无税/含税)或 ≈ 净额+7%(漏抽销项税)。
    # ★必须减折扣,否则误杀 7-11 类折扣票(小计115−折扣5=总额110·见 [[ocr-determinism-layer-root-cause]])。
    if vat is None and sub is not None and total is not None and sub > 0:
        net = sub - (discount or 0.0)
        diff = total - net
        expected_vat = net * _VAT_RATE
        ok_zero = abs(diff) <= _TOL
        ok_vat = abs(diff - expected_vat) <= max(_TOL, expected_vat * _RECON_REL)
        if not ok_zero and not ok_vat:
            reasons.append(
                f"缺 VAT 且总额 {total} != 净额 {net:.2f}(小计 {sub} − 折扣 {discount or 0}),"
                f"差 {diff:.2f} 既非 0 也非 7%({expected_vat:.2f}) — 勾稽不平"
            )

    return reasons
