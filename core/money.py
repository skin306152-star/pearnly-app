# -*- coding: utf-8 -*-
"""金额比较(跨域 · core 级)。

`amounts_equal` = 两金额精确相等(Decimal 逐位,避免 float 0.1+0.2 漂移)。不可解 → False。
无容差:对账域的约等(bank_recon AMOUNT_TOL / 分档容差)是另一套语义,不走这里。
调用点自己处理占位/空值放行(如推送快照 "-"、改错 cur or 0)——本函数只管"数值是否相等"。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


def amounts_equal(a, b) -> bool:
    """a、b 数值是否精确相等(Decimal)。任一不可解析 → False。"""
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except (InvalidOperation, TypeError, ValueError):
        return False
