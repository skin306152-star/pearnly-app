# -*- coding: utf-8 -*-
"""字段级修正 diff(纯函数,无 IO)。

比 AI 首存基线 pages 与用户编辑后 pages 的主页字段:值变了 = 一条用户修正。内部字段
(下划线开头,如 _suggested_client_*)、两侧皆空、纯空白差异不算。"""

from typing import Optional

# 只学这些业务字段的修正,跳过 pages 里的结构/内部键,避免噪声入库。
TRACKED_FIELDS = (
    "invoice_number",
    "invoice_date",
    "date",
    "seller_name",
    "seller_tax",
    "buyer_name",
    "buyer_tax",
    "total_amount",
    "subtotal",
    "vat",
    "wht",
    "category",
)


def _primary_fields(pages) -> dict:
    """取主页(首个非副本/非重复页)的 fields;退化到首页。"""
    for p in pages or []:
        if not p.get("is_copy") and not p.get("is_duplicate"):
            return p.get("fields") or {}
    if pages:
        return pages[0].get("fields") or {}
    return {}


def _norm(v) -> str:
    return "" if v is None else str(v).strip()


def compute_field_corrections(ai_pages, corrected_pages) -> list:
    """返回 [{field_name, ai_value, corrected_value}]。无修正 → []。"""
    ai = _primary_fields(ai_pages)
    cur = _primary_fields(corrected_pages)
    out = []
    for field in TRACKED_FIELDS:
        ai_v = _norm(ai.get(field))
        cur_v = _norm(cur.get(field))
        if cur_v and cur_v != ai_v:
            out.append({"field_name": field, "ai_value": ai_v or None, "corrected_value": cur_v})
    return out


def primary_seller(pages) -> tuple:
    """(seller_tax, seller_name) of primary page · 给例库按主体归集。"""
    f = _primary_fields(pages)
    tax: Optional[str] = _norm(f.get("seller_tax")) or None
    name: Optional[str] = _norm(f.get("seller_name")) or None
    return tax, name
