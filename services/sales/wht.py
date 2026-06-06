# -*- coding: utf-8 -*-
"""预扣税(WHT)多档(L2 · docs/16 §L2)。

泰国 WHT 按服务类型分档:1% 运输 / 2% 广告 / 3% 服务·专业费 / 5% 租金,加 0(不扣)与
自定义。本模块只提供档位清单 + 票面标签;金额仍由 compute_totals 按 wht_rate 算(单据级,
per-line 留后续)。WHT 抵扣凭证由付款方=买方出,不在本模块。纯常量叶子。
"""

from __future__ import annotations

from decimal import Decimal

# 预设档:(rate 字符串, 泰/英 服务类型标签)。前端下拉用;custom = 自由值(校验仍 0~100)。
WHT_PRESETS = (
    ("0", "ไม่หัก / None"),
    ("1", "ค่าขนส่ง / Transport"),
    ("2", "ค่าโฆษณา / Advertising"),
    ("3", "ค่าบริการ·วิชาชีพ / Service & Professional"),
    ("5", "ค่าเช่า / Rental"),
)


def _fmt_rate(rate) -> str:
    """档率去尾零:Decimal('3.00') → '3',Decimal('1.50') → '1.5'。"""
    d = Decimal(str(rate if rate not in (None, "") else 0))
    return format(d.normalize(), "f")


def pdf_label(rate) -> str:
    """票面 WHT 标签带档率(§L2):'หัก ณ ที่จ่าย 3% / WHT'。"""
    return f"หัก ณ ที่จ่าย {_fmt_rate(rate)}% / WHT"
