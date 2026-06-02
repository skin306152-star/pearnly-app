# -*- coding: utf-8 -*-
"""recon 路由跨组共享 helper（user key + 计费页数口径）· recon_routes 拆分。"""


def _user_key(user):
    return (user.get("gemini_api_key") or user.get("custom_gemini_api_key") or "").strip() or None


_ROWS_PER_PAGE_BILLING = 40  # v0.58 · 居中计费:一页约 40 笔 · 防密集账单按页低估


def _pdf_billing_units(page_count: int, row_count: int) -> int:
    """v118.35.0.58 · 银行对账 PDF/图片计费『页数』· 居中口径 max(实际页数, ⌈行数/N⌉)。
    对齐 ฿1.5/页规则 · 修复此前误按交易行数计费(超收 10-34 倍)的 bug。
    既不让多页大账单超收 · 也不让一页塞很多笔的密集账单被低估 · 图片=1 页。"""
    import math as _m

    pages = max(1, int(page_count or 0))
    rows = max(0, int(row_count or 0))
    return max(pages, _m.ceil(rows / _ROWS_PER_PAGE_BILLING))
