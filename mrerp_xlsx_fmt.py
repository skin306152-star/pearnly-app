# -*- coding: utf-8 -*-
"""MR.ERP xlsx · 字段格式工具 + 服务端校验上限常量 · mrerp_xlsx_generator 拆分 leaf.

铁律 29 字段格式(日期/字符串/金额)+ MR.ERP 服务端长度/日期/税种上限。纯函数,0 逻辑改。
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

# ============================================================
# 铁律 29 · 字段格式工具
# ============================================================
MAX_AMOUNT = Decimal("999999999.99")

# 服务端业务校验上限(2026-05-18 集成测试发现 · 见 mrerp-known-facts.md §7)
# xlsx schema 字段标 str(30) / str(50) 但 MR.ERP 服务端实际更严
# 校验顺序:服务端先做长度校验 → 长度过 → 才查主数据存在
# adapter 必须 client-side 拦截,避免 "ไม่พบ" 类错误被长度错遮盖
MRERP_INVOICE_NO_MAX = 18
MRERP_BILL_NO_MAX = 20
MRERP_CUSTOMER_CODE_MAX = 20
MRERP_CUSTOMER_BILL_MAX = 20

# sales_credit 允许的 Pearnly tax_kind 枚举(derive_tax_kind 的返回值之一)
# wht_* 是预扣税 · 销项发票不适用 · 仅 vat_* 或 non_vat 合法
MRERP_VALID_TAX_KINDS_SC = ("vat_7", "vat_0", "vat_exempt", "non_vat")

# 日期检查阈值(单位:天)
MRERP_DATE_FUTURE_HARD_REJECT_DAYS = 30  # > today + 30d → ERR_DATE_FUTURE
MRERP_DATE_FUTURE_WARN_DAYS = 7  # > today + 7d → 警告(不拒)
MRERP_DATE_PAST_WARN_DAYS = 730  # < today - 730d → 警告(2 年前)


def fmt_date(value: Any) -> str:
    """日期 → YYYY-MM-DD 字符串(cell 用 @ 文本格式)"""
    if not value:
        return ""
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return ""
        if len(s) >= 10 and s[4] == "-" and s[7] == "-":
            return s[:10]
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return s[:10]
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10]


def fmt_str(value: Any, max_len: int = 50) -> str:
    """字符串 trim 到 max_len · None / NaN 返回空串"""
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() in ("none", "null", "nan"):
        return ""
    if len(s) > max_len:
        return s[:max_len]
    return s


def fmt_number(value: Any) -> Optional[float]:
    """金额 → float · 超上限或非法返回 None · 负数静默 clamp 到 -MAX_AMOUNT
    (保留原行为:用于摘要/展示场景 · 不抛错)"""
    if value is None or value == "":
        return None
    try:
        n = Decimal(str(value))
    except Exception:
        return None
    if n > MAX_AMOUNT:
        return float(MAX_AMOUNT)
    if n < -MAX_AMOUNT:
        return float(-MAX_AMOUNT)
    return float(n)


def fmt_number_strict(value: Any) -> float:
    """金额严格模式 → float · 负数 / 超 MAX_AMOUNT / 非法都 raise ValueError
    用于 sales_credit 上传前 preflight · 销项发票净额必须 > 0
    (P1-A §3.3 · 2026-05-18)"""
    if value is None or value == "":
        raise ValueError("amount is missing")
    try:
        n = Decimal(str(value))
    except Exception as e:
        raise ValueError(f"amount not parseable: {value!r}") from e
    if n < 0:
        raise ValueError(
            f"negative amount {n} not allowed for sales_credit upload "
            "(use a credit-note flow instead)"
        )
    if n > MAX_AMOUNT:
        raise ValueError(
            f"amount {n} exceeds MR.ERP ceiling {MAX_AMOUNT}; " "split the invoice or escalate"
        )
    return float(n)
