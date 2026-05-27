# -*- coding: utf-8 -*-
"""Credits 计费 · 定价策略 + 成本估算(纯计算 · 无 DB · 无扣费)

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
PDF 分段阶梯价 + Excel/Word/CSV 按字符计价。db.charge_ocr 经 db.py 尾 re-export 调本模块
estimate_*(裸名解析到 db 命名空间的 re-export)· app/recon_*/services.ocr 走 db.estimate_* 不变。
"""

from decimal import Decimal as _DecV21, ROUND_HALF_UP as _RH_V21
import math as _math_v21

PDF_TIER1_LIMIT_V21 = 200
PDF_TIER1_PRICE_V21 = _DecV21("1.50")
PDF_TIER2_PRICE_V21 = _DecV21("0.75")
EXCEL_CHARS_PER_SATANG_V21 = 50
EXCEL_SATANG_PRICE_V21 = _DecV21("0.01")


def estimate_pdf_cost_thb(pages_used_this_month: int, page_count: int) -> _DecV21:
    """估算 PDF N 页的总成本 · 跨界自动拆段
    v0.21 改: 调用端传 pages_used_this_month · 不再查 DB · 与前置 combined 查询复用
    """
    n = max(0, int(page_count or 0))
    if n == 0:
        return _DecV21("0.00")
    used = max(0, int(pages_used_this_month or 0))
    tier1_remaining = max(0, PDF_TIER1_LIMIT_V21 - used)
    tier1_pages = min(n, tier1_remaining)
    tier2_pages = n - tier1_pages
    cost = (PDF_TIER1_PRICE_V21 * tier1_pages) + (PDF_TIER2_PRICE_V21 * tier2_pages)
    return cost.quantize(_DecV21("0.01"), rounding=_RH_V21)


def estimate_excel_cost_thb(char_count: int) -> _DecV21:
    """Excel/Word/CSV 按字符计费 · 50 字符 = 1 satang · 向上取整"""
    n = max(0, int(char_count or 0))
    if n == 0:
        return _DecV21("0.00")
    satang = _math_v21.ceil(n / EXCEL_CHARS_PER_SATANG_V21)
    return (EXCEL_SATANG_PRICE_V21 * satang).quantize(_DecV21("0.01"), rounding=_RH_V21)
