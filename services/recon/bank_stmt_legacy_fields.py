# -*- coding: utf-8 -*-
"""
services/recon/bank_stmt_legacy_fields.py · Pearnly

Field/amount/date helpers for the legacy bank-statement text parsers.
Pure functions, no module dependencies — the leaf of the legacy parse layer.
"""

import re
from datetime import date
from typing import Optional, Tuple


def _looks_like_outflow(desc: str) -> bool:
    """从描述判断是否为出账流水"""
    if not desc:
        return False
    u = desc.upper()
    out_kw = [
        "WITHDRAW",
        "WDRL",
        "FEE",
        "CHARGE",
        "PAY",
        "PAYMENT",
        "OUT",
        "DEBIT",
        "PURCHASE",
        "BUY",
        "ถอน",
        "ค่าธรรมเนียม",
        "ชำระ",
    ]
    return any(k in u or k in desc for k in out_kw)


# ============================================================
# 工具函数
# ============================================================
def _parse_amount(s: Optional[str]) -> Optional[float]:
    """'1,234.56' → 1234.56 · None / 空 → None"""
    if not s:
        return None
    try:
        return float(s.replace(",", "").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


def _normalize_thai_date(s: str, reference: Optional[str] = None) -> Optional[str]:
    """
    DD/MM/YY 或 DD/MM/YYYY → YYYY-MM-DD
    泰国银行对账单年份经常用佛历(+543)· 自动转公历
    若年份只有 2 位 · 用 reference 年推断
    """
    if not s:
        return None
    # 支持 / 和 -
    parts = re.split(r"[/\-]", s.strip())
    if len(parts) != 3:
        return None
    try:
        dd, mm, yy = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    # 年份归一化
    if yy < 100:
        # 2 位 · 推测:> 50 归 19xx,其余归 20xx · 泰国一般都是近期
        yy = 2000 + yy if yy < 70 else 1900 + yy
    elif yy > 2400:
        # 佛历 → 公历
        yy -= 543
    # 基本验证
    if not (1 <= mm <= 12 and 1 <= dd <= 31 and 2000 <= yy <= 2099):
        return None
    try:
        return date(yy, mm, dd).isoformat()
    except ValueError:
        return None


def _find_account_last4(text: str) -> Optional[str]:
    """从对账单头部找账号末 4 位"""
    # 匹配如 "Account No. xxx-x-xxxx1234" 或 "Acct XXX1234"
    patterns = [
        r"[Aa]ccount\s*(?:No|Number|#)?\.?\s*[:\s]*\S*?(\d{4})\b",
        r"[Aa]cct\.?\s*[:\s]*\S*?(\d{4})\b",
        r"เลขที่บัญชี\s*[:\s]*\S*?(\d{4})\b",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def _find_period(text: str) -> Tuple[Optional[str], Optional[str]]:
    """找对账周期起止 · 英文 'Period' / 泰文 'ประจำเดือน'"""
    # 'Period: 01/12/2024 - 31/12/2024'
    m = re.search(
        r"(?:Period|Statement\s*Period|Date\s*Range)[:\s]*"
        r"(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:-|to|ถึง)\s*(\d{1,2}/\d{1,2}/\d{2,4})",
        text,
        re.IGNORECASE,
    )
    if m:
        return _normalize_thai_date(m.group(1)), _normalize_thai_date(m.group(2))
    # 泰文格式:ตั้งแต่วันที่ X ถึง Y
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:-|ถึง|to)\s*(\d{1,2}/\d{1,2}/\d{2,4})", text)
    if m:
        return _normalize_thai_date(m.group(1)), _normalize_thai_date(m.group(2))
    return None, None


def _find_opening_closing(text: str) -> Tuple[Optional[float], Optional[float]]:
    """找期初 / 期末余额"""
    opening = None
    closing = None
    for pat in [
        r"[Oo]pening\s*[Bb]alance[:\s]*([\d,]+\.\d{2})",
        r"[Bb]rought\s*[Ff]orward[:\s]*([\d,]+\.\d{2})",
        r"ยอดยกมา[:\s]*([\d,]+\.\d{2})",
    ]:
        m = re.search(pat, text)
        if m:
            opening = _parse_amount(m.group(1))
            break
    for pat in [
        r"[Cc]losing\s*[Bb]alance[:\s]*([\d,]+\.\d{2})",
        r"[Cc]arried\s*[Ff]orward[:\s]*([\d,]+\.\d{2})",
        r"ยอดคงเหลือ[:\s]*([\d,]+\.\d{2})",
    ]:
        m = re.search(pat, text)
        if m:
            closing = _parse_amount(m.group(1))
            break
    return opening, closing


def _month_of(d_str: Optional[str]) -> Optional[str]:
    """'2024-12-15' → '2024-12-01'"""
    if not d_str:
        return None
    try:
        d = date.fromisoformat(d_str)
        return d.replace(day=1).isoformat()
    except ValueError:
        return None


def _guess_channel(desc: str) -> str:
    """根据描述猜测渠道类型"""
    if not desc:
        return ""
    u = desc.upper()
    if "ATM" in u:
        return "ATM"
    if "TRANSFER" in u or "TRF" in u or "โอน" in desc:
        return "TRANSFER"
    if "FEE" in u or "CHARGE" in u or "ค่าธรรมเนียม" in desc:
        return "FEE"
    if "CHEQUE" in u or "CHQ" in u or "เช็ค" in desc:
        return "CHEQUE"
    if "INTEREST" in u or "ดอกเบี้ย" in desc:
        return "INTEREST"
    if "SALARY" in u or "PAYROLL" in u or "เงินเดือน" in desc:
        return "SALARY"
    if "BILL" in u or "PAY" in u:
        return "BILLPAY"
    return ""
