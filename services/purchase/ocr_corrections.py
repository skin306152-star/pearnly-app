# -*- coding: utf-8 -*-
"""Deterministic OCR field cleanup before purchase drafts are built.

These rules only fix values that can be corrected from arithmetic or stable
Thai document conventions. Anything uncertain is left for review.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from services.purchase import field_clean

_CENT = Decimal("0.01")
_DATE_RE = re.compile(r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\s*$")
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TH_BRANCH_RE = re.compile(r"(?:สาขา|branch|br\.?)\D{0,12}(\d{3,5})", re.I)


def _dec(v: Any) -> Decimal:
    try:
        return Decimal(str(v).replace(",", "").strip()) if v not in (None, "") else Decimal("0")
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _money(v: Decimal) -> str:
    return format(v.quantize(_CENT), "f")


def _year_from_two_digits(yy: int) -> int:
    today_year = date.today().year
    candidates = [y for y in (2000 + yy, 2500 + yy - 543) if 2000 <= y <= today_year + 1]
    return min(candidates, key=lambda y: abs(today_year - y)) if candidates else 2000 + yy


def _normalize_date(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if _ISO_RE.match(raw):
        return raw
    m = _DATE_RE.match(raw)
    if not m:
        return raw
    day, month, year = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if year < 100:
        year = _year_from_two_digits(year)
    elif year >= 2400:
        year -= 543
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return raw


def _is_branch_number_as_invoice(fields: dict, invoice_no: str) -> bool:
    digits = re.sub(r"\D", "", invoice_no or "")
    if not digits or digits != str(invoice_no or "").strip() or len(digits) > 5:
        return False
    haystack = " ".join(str(fields.get(k) or "") for k in ("seller_name", "seller_addr", "notes"))
    for match in _TH_BRANCH_RE.finditer(haystack):
        if match.group(1).lstrip("0") == digits.lstrip("0"):
            return True
    return False


# 加油票品名(任一命中即按加油票走升×单价兜底)。泰/英混排,长词在前。
_FUEL_WORDS = (
    "ไฮดีเซล",
    "ดีเซล",
    "เบนซิน",
    "แก๊สโซฮอล",
    "แก็สโซฮอล",
    "โซฮอล",
    "น้ำมัน",
    "diesel",
    "gasohol",
    "benzine",
    "benzin",
    "petrol",
    "fuel",
)


def _is_fuel_line(name: Any) -> bool:
    low = str(name or "").lower()
    return any(w.lower() in low for w in _FUEL_WORDS)


def _fuel_total_from_lines(items: Any) -> Decimal:
    """加油票真实总额 = 升 × 升价(地面真相)。只认【加油品名 + qty 含小数(真升数·非整数积分/件)
    + 单价 > 0】的行;印刷行小计与升×单价一致(泵凑整 ≤ 1 铢)→ 取印刷小计(更准),否则取升×单价。

    积分行(qty=22 整数·คะแนน)绝不当升数 → 跳过(防 22 × 39.85 = 876 冒充总额)。无加油行 → 0。
    """
    for it in items or []:
        if not isinstance(it, dict) or not _is_fuel_line(it.get("name")):
            continue
        qty = _dec(it.get("qty"))
        price = _dec(it.get("price"))
        if qty <= 0 or price <= 0 or qty == qty.to_integral_value():
            continue
        calc = (qty * price).quantize(_CENT)
        sub = _dec(it.get("subtotal"))
        return sub if (sub > 0 and abs(sub - calc) <= Decimal("1")) else calc
    return Decimal("0")


def _is_vat_seven_percent(subtotal: Decimal, vat: Decimal) -> bool:
    if subtotal <= 0 or vat <= 0:
        return False
    expected = (subtotal * Decimal("0.07")).quantize(_CENT)
    return abs(expected - vat) <= Decimal("0.05")


def normalize_fields(fields: dict | None) -> dict:
    """Return a cleaned copy of OCR fields.

    Rules are deliberately conservative:
    - tax IDs keep only one visible 13-digit Thai ID;
    - branch numbers are not accepted as invoice numbers;
    - dates are normalized for common Thai DD/MM/YY and Buddhist-year formats;
    - missing subtotal/VAT/total is inferred only when arithmetic is exact.
    """
    src = dict(fields or {})
    out = dict(src)
    corrections: list[str] = list(src.get("_corrections") or [])

    # 税号:有效 13 位规范化;短数字/日期片段/含字母噪声(「13」「13/06/26」)→ 置空,不再残留。
    # 旧 bug:invalid 时返 '' 但「仅 truthy 才覆盖」→ 垃圾留在 out(详情页 เลขภาษี 显「13」)。
    for key in ("seller_tax", "buyer_tax"):
        raw = str(src.get(key) or "").strip()
        if not raw:
            continue
        cleaned = field_clean.clean_tax_id(raw)
        if cleaned != raw:
            out[key] = cleaned
            corrections.append(f"{key}_{'normalized' if cleaned else 'invalid_cleared'}")

    inv_no = str(src.get("invoice_number") or "").strip()
    if inv_no and _is_branch_number_as_invoice(src, inv_no):
        out["invoice_number"] = ""
        corrections.append("invoice_number_branch_removed")
    elif inv_no:
        out["invoice_number"] = inv_no

    norm_date = _normalize_date(src.get("date"))
    if norm_date != (src.get("date") or ""):
        out["date"] = norm_date
        corrections.append("date_normalized")

    # total 误取「现金收款额」而非应付净额(POS 小票常把 เงินสด/Cash 当 total · 7-11 实票)。
    # 票面同时印了 cash + change 且 total ≈ cash → 真应付 = cash − change,确定性校正(不信 LLM 选错列)。
    cash = _dec(src.get("cash_amount"))
    change = _dec(src.get("change_amount"))
    total = _dec(src.get("total_amount"))
    if cash > 0 and change > 0 and total > 0:
        net_paid = cash - change
        if net_paid > 0 and abs(total - cash) <= max(Decimal("1"), cash * Decimal("0.02")):
            total = net_paid
            out["total_amount"] = _money(total)
            corrections.append("total_fixed_from_cash_change")

    # 加油票总额读飞兜底:升 × 升价 是地面真相,LLM 常把净额读成圆整错值(Bangchak 1,780 → 1000)。
    # total 缺失或与升×单价偏差超容差 → 采信升×单价(印刷行小计一致时取印刷值更准)。积分行不计入。
    fuel_total = _fuel_total_from_lines(src.get("items"))
    if fuel_total > 0 and (
        total <= 0 or abs(total - fuel_total) > max(Decimal("1"), fuel_total * Decimal("0.02"))
    ):
        total = fuel_total
        out["total_amount"] = _money(total)
        corrections.append("fuel_total_from_qty_price")

    subtotal = _dec(src.get("subtotal"))
    vat = _dec(out.get("vat"))

    if subtotal <= 0 and total > 0 and vat > 0 and total >= vat:
        subtotal = total - vat
        out["subtotal"] = _money(subtotal)
        corrections.append("subtotal_inferred_from_total_vat")

    if vat <= 0 and subtotal > 0 and total > subtotal:
        diff = total - subtotal
        if _is_vat_seven_percent(subtotal, diff):
            vat = diff
            out["vat"] = _money(vat)
            corrections.append("vat_inferred_from_total_subtotal")

    if total <= 0 and subtotal > 0 and vat > 0:
        total = subtotal + vat
        out["total_amount"] = _money(total)
        corrections.append("total_inferred_from_subtotal_vat")

    if corrections:
        out["_corrections"] = sorted(set(corrections))
    return out
