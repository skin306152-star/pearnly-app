# -*- coding: utf-8 -*-
"""转换桥内部信号:一张 history 该跳过(非错误),不该拖累同批其它张。"""

from __future__ import annotations


class SkipConversion(Exception):
    """携带 reason 的跳过信号(purchase_leg/sales_leg 逐口径判定用)。"""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason
