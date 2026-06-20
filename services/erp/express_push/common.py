# -*- coding: utf-8 -*-
"""Express 载荷映射的共享纯函数(进项/销项共用 · 不连库 · 不调 LLM)。

进项 mapper 与销项 sales_mapper 都依赖这里:金额自洽求 (base,vat,total)、佛历日期、
科目解析、法人前缀、付款判定。钱一律 decimal,借贷/税额由确定性代码算
(见 [[line-accounting-honest-status-boundary]])。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

_CENT = Decimal("0.01")
_BALANCE_TOL = Decimal("0.02")  # 税前+税额 与 含税 容差
_VAT_RATE = Decimal("7")

# 泰国法人前缀(prename)· 按长度降序匹配(长的先,防 หจก. 被 ห้าง 短前缀截断)。
_PRENAMES = (
    "บริษัทจำกัด",
    "บริษัท",
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญ",
    "หจก.",
    "หจก",
    "หสน.",
)

# 付款字段里代表"已付/现金"的信号(归一小写匹配)。
_PAID_TOKENS = ("paid", "cash", "qr", "promptpay", "prompt_pay", "transfer", "เงินสด", "จ่ายแล้ว")


@dataclass(frozen=True)
class ExpressMapResult:
    """映射结果。ok=True → payload 可入队;ok=False → reason 落 manual 留人工。"""

    ok: bool
    payload: Optional[Dict[str, Any]]
    reason: str


def _d(v: Any) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v).replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def _q(v: Decimal) -> Decimal:
    return v.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def _s(v: Decimal) -> str:
    """decimal → 定点字符串(钱不用 float · 保两位)。"""
    return format(_q(v), "f")


def fail(reason: str) -> ExpressMapResult:
    return ExpressMapResult(False, None, reason)


def detect_prename(name: str) -> str:
    s = (name or "").strip()
    for p in _PRENAMES:
        if s.startswith(p):
            return p
    return ""


def payment_is_paid(fields: Dict[str, Any]) -> Optional[bool]:
    """票面是否已付:True 已付 / False 未付 / None 无信号(由各 mapper 定默认)。"""
    status = str(fields.get("payment_status") or "").strip().lower()
    if status == "paid":
        return True
    if status in ("unpaid", "credit"):
        return False
    method = str(fields.get("payment_method") or "").strip().lower()
    if method and any(tok in method for tok in _PAID_TOKENS):
        return True
    return None


def be_dates(invoice_date: Any) -> Optional[tuple[str, str]]:
    """公历 ISO 日期 → (docdate_be, vat_period_be)。无法解析 → None(缺日期不建账)。"""
    s = str(invoice_date or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        m2 = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$", s)  # DD/MM/YYYY
        if not m2:
            return None
        day, month, year = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
    else:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    yy = (year + 543) % 100
    return (f"{yy:02d}{month:02d}{day:02d}", f"{yy:02d}{month:02d}01")


def resolve_account(
    accounts: List[Dict[str, Any]], category: str, config_code: Optional[str]
) -> Optional[str]:
    """科目解析:先查映射束(erp_type=express · pearnly_category 命中),否则 config 兜底码。"""
    cat = (category or "").strip()
    if cat:
        for a in accounts or []:
            if (a.get("erp_type") or "").lower() == "express" and (
                a.get("pearnly_category") or ""
            ) == cat:
                code = (a.get("erp_code") or "").strip()
                if code:
                    return code
    code = (config_code or "").strip()
    return code or None


def amounts(fields: Dict[str, Any], history: Dict[str, Any]) -> Optional[tuple]:
    """从票面字段确定性求 (base, vat, total)。返回 None = 数不自洽/缺总额(留人工)。

    优先采信票面 税前+税额 自洽;缺 VAT 用 总额−税前;只有总额按 7% 含税反推。
    """
    from services.purchase.totals import vat_from_inclusive

    total = (
        _d(history.get("total_amount")) or _d(fields.get("total_amount")) or _d(fields.get("total"))
    )
    if total is None or total <= 0:
        return None
    base = _d(fields.get("subtotal"))
    vat = _d(fields.get("vat"))

    if base is not None and vat is not None and base > 0:
        pass
    elif base is not None and base > 0:
        vat = total - base
    elif vat is not None and vat >= 0:
        base = total - vat
    else:
        # 只有总额 → 按 7% 含税反推。
        vat = _q(vat_from_inclusive(total))
        base = total - vat

    base, vat, total = _q(base), _q(vat), _q(total)
    if base <= 0 or vat < 0:
        return None
    if abs(base + vat - total) > _BALANCE_TOL:
        return None
    return base, vat, total
