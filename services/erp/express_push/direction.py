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
    withdrawal)→ None,交给税号判定。

    fields.direction 是回导裁决落脚的地方(会计把行挪去哪张 Sheet)。此前只看记录顶层,
    而 ocr_history 压根没有 direction 列 —— 于是这个函数恒返 None,「挪一行 = 改一次
    分类」这条回导核心机制从未生效(2026-07-25 真机实锤)。
    """
    d = (
        str(
            (flat or {}).get("direction")
            or (history or {}).get("direction")
            or _fields(flat).get("direction")
            or ""
        )
        .strip()
        .lower()
    )
    if d in _SALES_TOKENS:
        return "sales"
    if d in _PURCHASE_TOKENS:
        return "purchase"
    return None


def normalize(value: Any) -> Optional[str]:
    """归一一个方向声明 → sales/purchase;认不出 → None(= 当没声明,交税号锚点判)。

    收料口的批级声明用它;判据(哪些词算销项/进项)与 explicit_direction 共用一套,
    不在两处各写一份 token 表。
    """
    return explicit_direction({"direction": value}, {})


def apply_batch_direction(fields: Optional[Dict[str, Any]], direction: Optional[str]) -> None:
    """把批级方向声明(录入向导 step① 选的)落进 fields.direction。原地改,无返回。

    已有值不覆盖:回导行的方向是会计**逐行**裁决的(他把行挪去了哪张 Sheet),
    比"整批选一个"更具体 —— 批级声明抹掉它就等于替会计把分类改回去。
    """
    if fields is None or not direction:
        return
    if not fields.get("direction"):
        fields["direction"] = direction


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
