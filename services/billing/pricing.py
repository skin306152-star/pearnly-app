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


# 订阅套餐目录:额度(张/周期)· 月费 · 超额单价(超出额度后每张从余额扣)。
# 周期 = 订阅日起 SUBSCRIPTION_CYCLE_DAYS 天 · 到期自动从余额续订(见 services/billing/subscription.py)。
SUBSCRIPTION_PLANS = {
    "S": {"quota": 100, "fee": _DecV21("150"), "over_rate": _DecV21("1.50")},
    "M": {"quota": 200, "fee": _DecV21("250"), "over_rate": _DecV21("1.25")},
    "L": {"quota": 500, "fee": _DecV21("500"), "over_rate": _DecV21("1.00")},
}
SUBSCRIPTION_CYCLE_DAYS = 30

# 文档(Excel/Word/CSV)按字符计费 · 折算成套餐「张」额度的基准价:
# 按量成本 ÷ DOC_QUOTA_REF_PRICE 向上取整 = 该文档占用的额度张数(与按量一档页价 ฿1.50 对齐 · 跨套餐一致)。
DOC_QUOTA_REF_PRICE = _DecV21("1.50")


def subscription_plan_spec(plan_code: str) -> dict | None:
    """套餐码(S/M/L · 大小写不敏感)→ {quota, fee, over_rate};未知码返 None。"""
    return SUBSCRIPTION_PLANS.get((plan_code or "").strip().upper())


def doc_quota_pages(char_count: int) -> int:
    """Excel/Word/CSV 文档折算成套餐额度张数:按量成本 ÷ ฿1.50 · 向上取整。

    PDF/图片按物理页数直接占额度(1 页 = 1 张),无需本函数;字符计费文档单位不一致才折算。
    """
    cost = estimate_excel_cost_thb(char_count)
    if cost <= 0:
        return 0
    return _math_v21.ceil(cost / DOC_QUOTA_REF_PRICE)
