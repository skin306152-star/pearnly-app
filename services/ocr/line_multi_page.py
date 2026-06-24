# -*- coding: utf-8 -*-
"""多页单据(PDF 含多张票)逐页入账的安全页序。

从 line_image_ocr 抽出(独立模块·避免巨石近上限再涨·便于纯函数单测)。
"""

from __future__ import annotations


def select_bookable_pages(pages, file_hash, *, flatten):
    """逐页入账的安全页序 → list[(fields, field_confidence, image_sha256)]。

    防长单跨页重复记账(伤账红线):跳过非票页;第一张可入账页必记,其后页须自带身份(卖家税号或
    票号·能参与去重的页)才记 —— 无身份续页跳过,否则同一发票会被重复记成多笔(同号续页另由 dedupe
    指纹兜底)。图片指纹只挂第一张(供 fastpath 重发短路),其余传 None 避免同 sha 多单碰撞。flatten 注入便于单测。
    """
    out = []
    booked = False
    for pg in pages:
        inv = getattr(pg, "invoice", None)
        if inv is None or getattr(inv, "is_not_invoice", False):
            continue
        fields = flatten(inv)
        has_identity = bool(
            str(fields.get("seller_tax") or "").strip()
            or str(fields.get("invoice_number") or "").strip()
        )
        if booked and not has_identity:
            continue
        out.append(
            (fields, getattr(pg, "field_confidence", None), file_hash if not booked else None)
        )
        booked = True
    return out
