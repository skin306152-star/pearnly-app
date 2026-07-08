# -*- coding: utf-8 -*-
"""汇总表日期归一:真实泰国销售汇总表的日期列千奇百怪,统一收成公历 ISO(YYYY-MM-DD),
交下游 be_dates 转佛历。三类真实场景(有数据自动认,认不出交人工补批次年月):

  1. 完整日期(2026-06-01 / 01/06/2026)→ 直接用(佛历年自动转公历)。
  2. 只有日号(1..31)→ 配批次"年月"(period)拼成完整日期。真实表年月常只写在标题行。
  3. 认不出 → None(缺日期不建账,判定层报 bad_date)。

佛历(พ.ศ.)判定:泰国汇总表年份普遍是佛历(2500+),公历-543。年份 ≥ 2400 视为佛历。
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

_BE_OFFSET = 543
_BE_THRESHOLD = 2400  # 年份 ≥ 此值视为佛历(泰国佛历今约 2560+,公历 2020+ 不会误判)

# 泰文月份(全称 + 常见缩写)→ 月。用于从标题行自动认出年月。
_THAI_MONTHS = {
    "มกราคม": 1,
    "ม.ค": 1,
    "กุมภาพันธ์": 2,
    "ก.พ": 2,
    "มีนาคม": 3,
    "มี.ค": 3,
    "เมษายน": 4,
    "เม.ย": 4,
    "พฤษภาคม": 5,
    "พ.ค": 5,
    "มิถุนายน": 6,
    "มิ.ย": 6,
    "กรกฎาคม": 7,
    "ก.ค": 7,
    "สิงหาคม": 8,
    "ส.ค": 8,
    "กันยายน": 9,
    "ก.ย": 9,
    "ตุลาคม": 10,
    "ต.ค": 10,
    "พฤศจิกายน": 11,
    "พ.ย": 11,
    "ธันวาคม": 12,
    "ธ.ค": 12,
}


def to_ad_year(year: int) -> int:
    """佛历 → 公历(≥2400 减 543);已是公历原样。"""
    return year - _BE_OFFSET if year >= _BE_THRESHOLD else year


def parse_full_date(cell: str) -> Optional[str]:
    """完整日期 → 公历 ISO(YYYY-MM-DD)。支持 YYYY-MM-DD / YYYY/MM/DD / DD-MM-YYYY。佛历自动转。"""
    s = (cell or "").strip()
    m = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)  # DD/MM/YYYY
        if not m:
            return None
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f"{to_ad_year(y):04d}-{mo:02d}-{d:02d}"


def resolve_date(cell: str, period: Optional[Tuple[int, int]]) -> Optional[str]:
    """一格日期 → 公历 ISO。完整日期直接归一;只有日号则配批次年月(公历 year, month)。认不出 → None。"""
    s = (cell or "").strip()
    if not s:
        return None
    full = parse_full_date(s)
    if full:
        return full
    if re.fullmatch(r"\d{1,2}", s) and period:
        day = int(s)
        yy, mm = period
        if 1 <= day <= 31 and 1 <= mm <= 12:
            return f"{yy:04d}-{mm:02d}-{day:02d}"
    return None


def detect_period(text: str) -> Optional[Tuple[int, int]]:
    """从标题/前言文字自动认出(公历 year, month)。命中泰文月名 + 4 位年份则返回,否则 None。"""
    if not text:
        return None
    low = text.lower()
    month = next((m for name, m in _THAI_MONTHS.items() if name in low), None)
    ym = re.search(r"(\d{4})", text)
    if month and ym:
        return to_ad_year(int(ym.group(1))), month
    return None
