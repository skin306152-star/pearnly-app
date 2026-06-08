# -*- coding: utf-8 -*-
"""进项单据金额计算(纯函数叶子 · 不连库 · docs/purchasing/01 §合计)。

逐字镜像前端 src/home/purchase-calc.js(computePurchaseTotals)的算法,保证录入屏即时合计
== 后端权威合计(同 POS totals.py ↔ pos-totals.js 范式)。全程 Decimal 分位 + ROUND_HALF_EVEN
(半偶数,镜像 JS q2c)。VAT/WHT 逐行取整后求和(非先汇总后取整),防 ±1 分漂移(餐厅服务费教训)。

合计链:行 gross→行折扣→行净额(≥0)→Σ=税前小计;VAT/WHT 各行净额逐行取整求和;
整单折扣只减 base(不重算 VAT,对齐前端);含税合计=base+VAT+凑整;实付=含税−WHT。
"""

from __future__ import annotations

import hashlib
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _d(v: Any) -> Decimal:
    try:
        return Decimal(str(v if v is not None else 0))
    except (ValueError, ArithmeticError):
        return Decimal("0")


def _q(v: Decimal) -> Decimal:
    """分位量化 · 半偶数舍入(镜像前端 q2c)。"""
    return v.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def compute_purchase_totals(lines, *, doc_discount=0, rounding=0) -> dict:
    """从明细行算进项合计 + 规整行(带 line_total/line_no)。镜像前端逐行取整。

    行入参:{item_type,product_id,description,qty,unit,unit_price,discount,vat_rate,
    vat_applicable,wht_rate,category_id,subcategory_id,batch_no,expiry_date}。
    vat_applicable=False 的行 VAT 率按 0 计(不抵)。
    """
    subtotal = Decimal("0")
    vat = Decimal("0")
    wht = Decimal("0")
    norm = []
    for i, ln in enumerate(lines or [], start=1):
        gross = _q(_d(ln.get("qty", 0)) * _d(ln.get("unit_price", 0)))
        line_disc = _q(_d(ln.get("discount", 0)))
        net = gross - line_disc
        if net < 0:
            net = Decimal("0.00")
        subtotal += net
        vat_rate = _d(ln.get("vat_rate", 0)) if ln.get("vat_applicable", True) else Decimal("0")
        wht_rate = _d(ln.get("wht_rate", 0))
        vat += _q(net * vat_rate / _HUNDRED)
        wht += _q(net * wht_rate / _HUNDRED)
        norm.append(
            {
                "line_no": i,
                "item_type": (ln.get("item_type") or "goods"),
                "product_id": ln.get("product_id"),
                "description": (ln.get("description") or "").strip(),
                "qty": _d(ln.get("qty", 0)),
                "unit": ln.get("unit"),
                "unit_price": _d(ln.get("unit_price", 0)),
                "discount": line_disc,
                "line_total": net,
                "vat_rate": vat_rate,
                "vat_applicable": bool(ln.get("vat_applicable", True)),
                "wht_rate": wht_rate,
                "category_id": ln.get("category_id"),
                "subcategory_id": ln.get("subcategory_id"),
                "batch_no": ln.get("batch_no"),
                "expiry_date": ln.get("expiry_date"),
            }
        )

    doc_disc = _q(_d(doc_discount))
    round_adj = _q(_d(rounding))
    base = subtotal - doc_disc
    if base < 0:
        base = Decimal("0.00")
    grand = base + vat + round_adj
    net_payable = grand - wht
    return {
        "subtotal": _q(subtotal),
        "discount_total": doc_disc,
        "vat_amount": _q(vat),
        "wht_amount": _q(wht),
        "rounding": round_adj,
        "grand_total": _q(grand),
        "net_payable": _q(net_payable),
        "lines": norm,
    }


def dedupe_key(*, supplier_tax, doc_no, grand_total) -> str | None:
    """防重复票指纹 = hash(供应商税号 | 票号 | 含税合计)。无税号且无票号 → None(无身份不查重)。

    费用单(LINE 一句话)常无票号/税号 → None,不参与去重(避免误拦)。
    """
    tax = str(supplier_tax).strip() if supplier_tax else ""
    no = str(doc_no).strip() if doc_no else ""
    if not tax and not no:
        return None
    total = format(_q(_d(grand_total)), "f")
    raw = f"{tax}|{no}|{total}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
