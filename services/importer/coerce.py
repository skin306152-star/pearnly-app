# -*- coding: utf-8 -*-
"""
Pearnly · 通用导入器 · 值coercion 叶子工具(REFACTOR-WA-B1 · 2026-05-29 从 template_learning 抽出)

纯搬家 0 逻辑改 · 叶子模块(只依赖 stdlib · 不 import 本包其它模块 · 防循环)。
template_learning / ai_mapping / gl 推断等都从这里 import 这组原语:
  · _norm          表头/值归一化(小写 + 折叠空白)
  · hit            提示词命中(短 ASCII 整词 · 长词/泰中日子串)
  · to_float       金额解析(千分位/括号负/泰式)
  · parse_date     日期解析(常见格式 + 泰历 年>2400 −543)
  · is_date_like / is_amount_like  形状判定
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Optional


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def hit(header: Any, hints) -> bool:
    """短 ASCII 词(in/out/cr/dr)整词匹配防误命中;长词/泰中日越用子串。"""
    h = _norm(header)
    if not h:
        return False
    tokens = None
    for hint in hints:
        hl = hint.lower()
        if hl.isascii() and len(hl) <= 3:
            if tokens is None:
                tokens = set(re.split(r"[\s/().,_\-]+", h))
            if hl in tokens:
                return True
        elif hl in h:
            return True
    return False


def to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "").replace(" ", "").replace(" ", "")
    if not s or s in {"-", "–", "—"}:
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s.startswith("-"):
        neg, s = True, s[1:]
    if s.count(".") > 1:  # 1.234.56 千分点
        first, *rest = s.split(".")
        s = first + "".join(rest[:-1]) + "." + rest[-1]
    try:
        out = float(s)
        return -out if neg else out
    except Exception:
        return 0.0


def parse_date(value: Any) -> Optional[date]:
    """支持常见格式 + 泰历(年>2400 → −543)。"""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        d = value.date()
        return date(d.year - 543, d.month, d.day) if d.year > 2400 else d
    if isinstance(value, date):
        return date(value.year - 543, value.month, value.day) if value.year > 2400 else value
    text = re.sub(r"\s+00:00:00$", "", str(value).strip())
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            d = datetime.strptime(text[:10], fmt).date()
            return date(d.year - 543, d.month, d.day) if d.year > 2400 else d
        except Exception:
            pass
    return None


def is_date_like(v: Any) -> bool:
    return parse_date(v) is not None


def is_amount_like(v: Any) -> bool:
    if v is None or str(v).strip() == "":
        return False
    return to_float(v) != 0.0 or str(v).strip() in {"0", "0.0", "0.00"}
