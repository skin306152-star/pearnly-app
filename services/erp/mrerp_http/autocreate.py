# -*- coding: utf-8 -*-
"""推送热路自建主数据 · 缺买方客户/商品 → 自动建 → 把 ERP 码注入 mappings 供发票生成器用。

设计:码取确定性值(客户=买方税号 / 商品=名 md5)→ 幂等(已存在则 create_* 视为成功);建成功
才注入 mappings(失败不注入 → 发票推到 ERP 会因"不存在"干净失败,不写脏)。默认开,
mappings['_mrerp_auto_create_customer'/'_mrerp_auto_create_product']=False 可关。仅销项触发。
"""

import hashlib
import re
from typing import Any, Dict, Iterable, List

from services.erp.mrerp_xlsx_lookups import (
    _build_product_lookup,
    _resolve_product_code,
    lookup_customer_code,
)


def _buyer_from_history(h: Dict[str, Any]) -> Dict[str, str]:
    """从 OCR history 抽买方(客户)· 码优先用税号(确定性幂等),无税号回退 client_id。"""
    fields = h.get("fields") if isinstance(h.get("fields"), dict) else {}

    def pick(*keys: str) -> str:
        for k in keys:
            v = h.get(k) or (fields.get(k) if isinstance(fields, dict) else None)
            if v:
                return str(v).strip()
        return ""

    tax = re.sub(r"\D", "", pick("customer_tax_id", "buyer_tax_id", "tax_id"))[:20]
    code = tax or ("C" + str(h.get("client_id") or "0"))
    return {
        "code": code[:20],
        "name": pick("customer_name", "buyer_name", "customer") or "-",
        "tax_id": tax,
        "address": pick("customer_address", "buyer_address", "address"),
        "phone": pick("customer_phone", "phone"),
        "email": pick("customer_email", "email"),
    }


def provision_customers(adapter, valid: List[Dict[str, Any]], mappings: Dict[str, Any]) -> None:
    """缺买方客户则自建 · 建成功把码注入 mappings['clients'](原地)。"""
    if not isinstance(mappings, dict) or not mappings.get("_mrerp_auto_create_customer", True):
        return
    pending: Dict[str, Dict[str, str]] = {}
    inject: List[tuple] = []
    for h in valid:
        cid = int(h.get("client_id") or 0)
        if lookup_customer_code(cid, mappings):
            continue  # 已映射,跳过
        buyer = _buyer_from_history(h)
        if not buyer["code"]:
            continue
        pending.setdefault(buyer["code"], buyer)
        inject.append((cid, buyer["code"]))
    if not pending:
        return
    results = adapter.create_customers(list(pending.values()), mappings)
    clients = mappings.setdefault("clients", [])
    for cid, code in inject:
        if results.get(code):
            clients.append({"erp_type": "mrerp", "client_id": cid, "erp_code": code})


def _iter_items(h: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """从 history 抽商品行(items / fields.items / pages[].fields.items · 同明细装配口径)。"""
    fields = h.get("fields") if isinstance(h.get("fields"), dict) else {}
    for src in (h.get("items"), fields.get("items") if isinstance(fields, dict) else None):
        if isinstance(src, list) and src:
            yield from (it for it in src if isinstance(it, dict))
            return
    for p in h.get("pages") or []:
        pf = p.get("fields") if isinstance(p, dict) else None
        pi = pf.get("items") if isinstance(pf, dict) else None
        if isinstance(pi, list) and pi:
            yield from (it for it in pi if isinstance(it, dict))
            return


def _product_code_from_name(name: str) -> str:
    """商品名 → 确定性商品码(≤15 · 幂等:同名同码 → create_products 重复视为成功)。"""
    # md5 仅作确定性短码派生,非安全用途 → usedforsecurity=False(过 bandit)
    digest = hashlib.md5(name.strip().lower().encode("utf-8"), usedforsecurity=False).hexdigest()
    return ("P" + digest)[:12].upper()


def provision_products(adapter, valid: List[Dict[str, Any]], mappings: Dict[str, Any]) -> None:
    """明细行对不上已有商品则自建 · 建成功把码注入 mappings['products'](原地)。"""
    if not isinstance(mappings, dict) or not mappings.get("_mrerp_auto_create_product", True):
        return
    lookup = _build_product_lookup(mappings)
    pending: Dict[str, Dict[str, Any]] = {}
    inject: List[tuple] = []
    for h in valid:
        for item in _iter_items(h):
            name = str(item.get("name") or item.get("description") or "").strip()
            if not name or _resolve_product_code(name, lookup):
                continue
            code = _product_code_from_name(name)
            pending.setdefault(
                code,
                {
                    "code": code,
                    "name": name,
                    "price": item.get("unit_price") or item.get("price") or 0,
                },
            )
            inject.append((name, code))
    if not pending:
        return
    results = adapter.create_products(list(pending.values()), mappings)
    products = mappings.setdefault("products", [])
    for name, code in inject:
        if results.get(code):
            products.append({"item_name": name, "erp_code": code})
