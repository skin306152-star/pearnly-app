# -*- coding: utf-8 -*-
"""发票方向自动判定(确定性 · 不靠 LLM · 税号锚点)。

云端只有银行流水带 deposit/withdrawal 方向,发票本身无进项/销项标签 → 现有
enqueue._direction_of 恒缺省 purchase,销项永远推不出去。本模块用「自家公司税号」当锚点,
比对票面 seller/buyer 税号确定性判向:

  自家 == 卖方  → 销项 sales
  自家 == 买方  → 进项 purchase
  两边都对不上 / 自家或票面税号没读到 / 两边都命中 → ambiguous(None · 不自动推,留人工)

显式方向(用户确认 / 已带 sales|purchase 标签)优先于税号判定。锚点税号由调用方从
workspace_clients(账套主体 · 即"卖方抬头")解析后传入,本模块只做纯比对。

多公司扩展位(v1 单公司):own_tax_id 将来可换成「本 workspace 客户公司税号集合」,
命中时同时得出「哪家公司(账套)+ 方向」—— 见 detect_by_tax 注释。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from services.purchase.field_clean import clean_tax_id

_SALES_TOKENS = ("sales", "income")
_PURCHASE_TOKENS = ("purchase", "expense")


def _fields(flat: Dict[str, Any]) -> Dict[str, Any]:
    f = (flat or {}).get("fields")
    return f if isinstance(f, dict) else {}


def explicit_direction(flat: Dict[str, Any], history: Dict[str, Any]) -> Optional[str]:
    """已带的进项/销项标签(用户确认等)→ 归一 sales/purchase;其它(含银行 deposit/
    withdrawal)→ None,交给税号判定。"""
    d = str((flat or {}).get("direction") or (history or {}).get("direction") or "").strip().lower()
    if d in _SALES_TOKENS:
        return "sales"
    if d in _PURCHASE_TOKENS:
        return "purchase"
    return None


def detect_by_tax(flat: Dict[str, Any], own_tax_id: Any) -> Optional[str]:
    """自家税号 × 票面 seller/buyer 税号 → sales/purchase/None(ambiguous)。

    多公司扩展:把 own_tax_id 换成集合并返回 (company, direction) —— 命中卖方那家即销项、
    命中买方那家即进项;v1 单公司锚点先返方向,company 由调用方已知账套给。

    税号经 clean_tax_id 归一(恰好 13 位否则 ''·与 mapper/sales_mapper 同口径):弱信号
    (OCR 残留如 '13')判 '' → 不匹配 → ambiguous,绝不靠脏税号误路由。
    """
    own = clean_tax_id(own_tax_id)
    if not own:
        return None
    fields = _fields(flat)
    seller = clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id"))
    buyer = clean_tax_id(fields.get("buyer_tax") or fields.get("buyer_tax_id"))
    match_seller = bool(seller) and seller == own
    match_buyer = bool(buyer) and buyer == own
    if match_seller and not match_buyer:
        return "sales"
    if match_buyer and not match_seller:
        return "purchase"
    return None  # 都不命中 / 都命中 / 没读到 → 留人工


def resolve_direction(
    flat: Dict[str, Any], history: Dict[str, Any], *, own_tax_id: Any
) -> Optional[str]:
    """显式方向优先,否则税号锚点判定。返回 sales/purchase 或 None(ambiguous)。"""
    return explicit_direction(flat, history) or detect_by_tax(flat, own_tax_id)
