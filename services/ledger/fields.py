# -*- coding: utf-8 -*-
"""松散字段取值 —— 同一张票的字段在仓里有三种来源(OCR 的 ThaiInvoice、回导解析器、
汇总表导入),键名各不相同。取值口径只此一处,各处各写一套就会漂。
"""

from __future__ import annotations

from typing import Any, Mapping

# 上游把字段 JSON 化时的几种「空」写法。当成有值会让 "None" 变成合法的客户名。
_NULLISH = ("none", "null", "nan")


def text(value: Any) -> str:
    """字段 → 干净字符串;空值写法一律归空串。"""
    if value is None:
        return ""
    s = str(value).strip()
    return "" if s.lower() in _NULLISH else s


def pick(fields: Mapping[str, Any], *keys: str) -> Any:
    """按给定顺序取第一个非空值 —— 顺序即优先级,别改成遍历 dict。"""
    for k in keys:
        v = fields.get(k)
        if v not in (None, ""):
            return v
    return None


def pick_text(fields: Mapping[str, Any], *keys: str) -> str:
    return text(pick(fields, *keys))
