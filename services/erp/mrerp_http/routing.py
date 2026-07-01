# -*- coding: utf-8 -*-
"""任意单据 → 方向(销/采)→ MR.ERP doc_type。

复用 Express 侧确定性方向判定(services/erp/express_push/direction · 税号锚点 · 不靠 LLM):
套账主体税号 == 卖方 → 销项;== 买方 → 采购;两边都对不上/都命中 → ambiguous(None,留人工)。
方向再按付款状态细分成具体导入模块(见 modules.MODULES):
  销项:已付/现金 → sales_cash;否则 → sales_credit
  采购:purchase(货品)

只做纯映射;own_tax_id 由调用方从套账主体解析后传入。doc_type=None 时调用方不自动推(留人工)。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from services.erp.express_push.common import payment_is_paid
from services.erp.express_push.direction import resolve_direction
from services.purchase.field_clean import clean_tax_id


def _fields(flat: Dict[str, Any]) -> Dict[str, Any]:
    f = (flat or {}).get("fields")
    return f if isinstance(f, dict) else {}


def choose_doc_type(
    flat: Dict[str, Any], history: Dict[str, Any], *, own_tax_id: Any
) -> Optional[str]:
    """套账主体税号 × 票面买卖方 → sales_credit / sales_cash / purchase / None(ambiguous)。"""
    direction = resolve_direction(flat, history, own_tax_id=own_tax_id)
    if direction == "sales":
        return "sales_cash" if payment_is_paid(_fields(flat)) else "sales_credit"
    if direction == "purchase":
        return "purchase"
    return None


def confirmed_account_set_mismatch(
    flat: Dict[str, Any], history: Dict[str, Any], *, own_tax_id: Any, expected_direction: str
) -> bool:
    """能【确认】这张票不属于本套账吗?防"把别家的票推错套账"的安全闸。

    只在【确认不符】时返 True(挡下),读不到税号=无法确认→False(不挡·交上游已判的方向)。
    确认不符 = ① 方向刚好相反(如采购票走销项)· 或 ② 票面读到了买卖方税号但都不是套账主体。
    own_tax_id 空(套账税号未解析)→ 无锚点无法判 → False(不挡)。
    """
    if not own_tax_id:
        return False
    direction = resolve_direction(flat, history, own_tax_id=own_tax_id)
    if direction == expected_direction:
        return False  # 确认属于本套账
    if direction:
        return True  # 方向相反(采购票走销项等)→ 确认不符
    # direction=None(ambiguous):仅当票面确实读到买卖方税号、却都不是套账主体,才算确认别家的票
    own = clean_tax_id(own_tax_id)
    fields = _fields(flat)
    read = [
        t
        for t in (
            clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id")),
            clean_tax_id(fields.get("buyer_tax") or fields.get("buyer_tax_id")),
        )
        if t
    ]
    return bool(read) and own not in read
