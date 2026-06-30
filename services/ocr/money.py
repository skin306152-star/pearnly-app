# -*- coding: utf-8 -*-
"""services/ocr/money.py · OCR/发票域钱字段归一(单一事实源)。

sanity 硬闸(热路径)与 invoice eval 打分器共用同一支金额/税号解析,避免两处各写一份
逐渐漂移。正则模块级编译(热路径每页调多次)。

注:银行/对账域另有 _to_float(None→0.0 语义),与此处(None→None)有意不同,各自独立。
"""

from __future__ import annotations

import re
from typing import Any, Optional

_RE_NON_MONEY = re.compile(r"[^\d.\-]")
_RE_NON_DIGIT = re.compile(r"\D")


def normalize_money(v: Any) -> Optional[float]:
    """'1,780.00' / '฿1780' / 1780 → float;空/不可解 → None。"""
    if v is None:
        return None
    s = _RE_NON_MONEY.sub("", str(v).replace(",", "").strip())
    if not s or s in ("-", ".", "-."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def normalize_id(v: Any) -> str:
    """税号/单号只留数字(票面常带空格/连字符:0-7355-27000-28-9)。"""
    return _RE_NON_DIGIT.sub("", str(v or ""))


def valid_thai_tax_id(v: Any) -> bool:
    """泰国 13 位税号 MOD-11 校验位:末位 = 前 12 位加权和的校验码。先归一去分隔符;
    非 13 位纯数字一律 False。算法同 services/knowledge/rules/validity(各域独立·不跨域耦合)。"""
    s = normalize_id(v)
    if len(s) != 13:
        return False
    digits = [int(c) for c in s]
    weighted = sum(digits[i] * (13 - i) for i in range(12))
    return digits[12] == (11 - (weighted % 11)) % 10
