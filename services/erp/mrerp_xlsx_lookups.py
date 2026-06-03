# -*- coding: utf-8 -*-
"""MR.ERP xlsx · 商品名归一化/映射查表 + 客户/科目/税种 mapping 查表 + tax_kind 推断.

mrerp_xlsx_generator 拆分 leaf。纯函数,0 逻辑改。商品归一化规则须与 db.py 的
_product_name_norm_for_db 完全一致(才能命中映射表的 item_name_norm 列)。
"""

import re
from typing import Any, Dict, Optional

from services.erp.mrerp_xlsx_fmt import fmt_str

# ============================================================
# v27.8.1.17 · 商品名归一化 + 映射查表(给 detail 行写真 product_code 用)
#   - 归一化规则跟 db.py 的 _product_name_norm_for_db 完全一致(必须一致才能命中映射表的 item_name_norm 列)
#   - mappings['products'] 是 db.get_mrerp_mappings_bundle 返的 list · 每项含 item_name_norm / erp_code
#   - 找不到返 None · 调用方 fallback '123' 占位
# ============================================================
_PRODUCT_NAME_NORM_RE = re.compile(r"[\s\.,\-_/\\()&\"'`*]+")


def _norm_product_name(s: Any) -> str:
    if not s:
        return ""
    out = _PRODUCT_NAME_NORM_RE.sub("", str(s))
    return out.lower().strip()[:256]


def _build_product_lookup(mappings: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """从 mappings['products'] 建 item_name_norm → erp_code 查表
    map 的 key 用归一化形式 · 跟 erp_product_mappings.item_name_norm 列一致
    """
    out: Dict[str, str] = {}
    if not mappings:
        return out
    products = mappings.get("products") if isinstance(mappings, dict) else None
    if not isinstance(products, list):
        return out
    for p in products:
        if not isinstance(p, dict):
            continue
        erp_code = p.get("erp_code")
        if not erp_code:
            continue
        # 2026-05-26 修:同时按【item_name 现算的 _norm_product_name】+【存的 item_name_norm】
        # 双 key 入表。根因:自动建档 _upsert_mapping 存的 item_name_norm 用的是
        # normalize_item_name(带空格),而 _resolve_product_code 查表用 _norm_product_name
        # (去空格)· 两套归一不一致 → 查不到 → 回退占位码 123 → 复核 NAME_MISMATCH ·
        # 自动建出的商品永远推不成。现算 key 保证 resolve 必命中,存的 key 留兼容。
        code = str(erp_code).strip()
        item_name = p.get("item_name") or ""
        for k in {_norm_product_name(item_name), (p.get("item_name_norm") or "")}:
            if k:
                out[k] = code
    return out


def _resolve_product_code(item_name: Any, lookup: Dict[str, str]) -> Optional[str]:
    """OCR item_name → ERP product code · 找不到返 None
    需配合 _build_product_lookup(mappings) 一起用 · 在 detail rows 循环外建 lookup 一次 · 内循环 O(1) 查表
    """
    if not item_name or not lookup:
        return None
    norm = _norm_product_name(item_name)
    return lookup.get(norm) if norm else None


# ============================================================
# Mapping 拼装(读 v118.27.0 的 3 张表)
# ============================================================
def lookup_customer_code(client_id: int, mappings: Dict[str, Any]) -> str:
    """从 erp_client_mappings 拿当前 client 在 mrerp 下的代码 · 没配返回空"""
    cli = (mappings or {}).get("clients") or []
    for m in cli:
        if m.get("erp_type") == "mrerp" and int(m.get("client_id") or 0) == int(client_id or 0):
            return fmt_str(m.get("erp_code"), 50)
    return ""


def lookup_account_code(category: str, mappings: Dict[str, Any]) -> str:
    acc = (mappings or {}).get("accounts") or []
    for m in acc:
        if m.get("erp_type") == "mrerp" and m.get("pearnly_category") == category:
            return fmt_str(m.get("erp_code"), 50)
    return ""


def lookup_tax_code(tax_kind: str, mappings: Dict[str, Any]) -> str:
    """从 erp_tax_mappings 拿税种字符串(铁律 29 · 税率字符串枚举)"""
    tax = (mappings or {}).get("taxes") or []
    for m in tax:
        if m.get("erp_type") == "mrerp" and m.get("pearnly_tax_kind") == tax_kind:
            return fmt_str(m.get("erp_code"), 14)
    return ""


def derive_tax_kind(history: Dict[str, Any]) -> str:
    """从 OCR 结果推断 Pearnly tax_kind 枚举"""
    rate = history.get("tax_rate_pct") or history.get("vat_rate")
    wht = history.get("wht_rate_pct") or history.get("wht_rate")
    try:
        if wht:
            w = int(float(wht))
            return f"wht_{w}" if w in (1, 3, 5) else "wht_3"
    except Exception:
        pass
    try:
        if rate is not None:
            r = float(rate)
            if r == 7:
                return "vat_7"
            if r == 0:
                return "vat_0"
            if r < 0:
                return "vat_exempt"
    except Exception:
        pass
    return "vat_7"
