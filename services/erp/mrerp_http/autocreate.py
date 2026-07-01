# -*- coding: utf-8 -*-
"""推送热路自建主数据 · 缺买方客户 → 自动建 → 把 ERP 码注入 mappings 供发票生成器用。

设计:客户码取买方税号(确定性 · 幂等 —— 已存在则 create_customers 视为成功);建成功才注入
mappings['clients'],失败不注入(发票推到 ERP 会因"客户不存在"干净失败,不写脏)。默认开,
mappings['_mrerp_auto_create_customer']=False 可关。仅销项(买方=客户)触发。
"""

import re
from typing import Any, Dict, List

from services.erp.mrerp_xlsx_lookups import lookup_customer_code


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
