# -*- coding: utf-8 -*-
"""推送热路自建主数据 · 缺买方客户/商品 → 自动建 → 把 ERP 码注入 mappings 供发票生成器用。

设计:码取确定性值(客户=买方税号 / 商品=名 md5)→ 幂等(已存在则 create_* 视为成功);建成功
才注入 mappings(失败不注入 → 发票推到 ERP 会因"不存在"干净失败,不写脏)。默认开,
mappings['_mrerp_auto_create_customer'/'_mrerp_auto_create_product']=False 可关。仅销项触发。
"""

import hashlib
import re
from typing import Any, Dict, Iterable, List

from services.erp import mrerp_xlsx_fmt as fmt
from services.erp.mrerp_xlsx_lookups import (
    MRERP_CASH_CUSTOMER,
    _build_product_lookup,
    _resolve_product_code,
    lookup_customer_code,
)
from services.erp.mrerp_xlsx_purchase import EXPENSE_ITEM_CODE_DEFAULT, expense_cfg


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
    cash_fallback = mappings.get("_mrerp_cash_customer_fallback", True)
    pending: Dict[str, Dict[str, str]] = {}
    inject: List[tuple] = []
    for h in valid:
        cid = int(h.get("client_id") or 0)
        if not cid:
            # 散客销项(无 client_id)→ 幂等确保通用现金客户存在,不按空买方建垃圾码。
            # 无需注入 clients 映射:resolve_customer_code 对 cid=0 直接返 เงินสด。
            if cash_fallback:
                pending.setdefault(
                    MRERP_CASH_CUSTOMER,
                    {"code": MRERP_CASH_CUSTOMER, "name": MRERP_CASH_CUSTOMER, "tax_id": ""},
                )
            continue
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


def _seller_from_history(h: Dict[str, Any]) -> Dict[str, str]:
    """从 OCR history 抽卖方(供应商)· 码优先用卖方税号(确定性幂等),无税号回退 client_id。"""
    fields = h.get("fields") if isinstance(h.get("fields"), dict) else {}

    def pick(*keys: str) -> str:
        for k in keys:
            v = h.get(k) or (fields.get(k) if isinstance(fields, dict) else None)
            if v:
                return str(v).strip()
        return ""

    tax = re.sub(r"\D", "", pick("seller_tax", "seller_tax_id", "supplier_tax_id"))[:20]
    name = pick("seller_name", "supplier_name", "seller")
    # 码推导链与 mrerp_xlsx_purchase._supplier_code 严格同源:税号 → 名字派生(零售
    # 小票常态卖方无税号 · 真机语料 SISTER MAKEUP)→ V+client_id。旧 "V0" 兜底删除:
    # 无税号无名无 client 建出共享垃圾码,preflight 又解析不到,建了白建。
    cid = h.get("client_id")
    code = tax or fmt.supplier_code_from_name(name) or (("V" + str(cid)) if cid else "")
    return {
        "code": code[:20],
        "name": name or "-",
        "tax_id": tax,
        "address": pick("seller_address", "supplier_address"),
        "phone": pick("seller_phone", "phone"),
        "email": pick("seller_email", "email"),
    }


def provision_suppliers(adapter, valid: List[Dict[str, Any]], mappings: Dict[str, Any]) -> None:
    """采购缺供应商则自建(幂等)· **不注入 mappings['suppliers']**。

    不注入的两条 why(2026-07-09 真机实锤):① 冗余——_supplier_code 的兜底链(税号→
    名字派生→V+cid)与 _seller_from_history 严格同源,自建的码本来就能从票面重导出;
    ② 注入行按 client_id 匹配,同 client_id 多个无税号卖家时后续票全解析到第一行的码
    (三张不同卖家的票落库后供应商全成同一家)。用户在 DB 配置的映射不受影响,照常优先。
    """
    if not isinstance(mappings, dict) or not mappings.get("_mrerp_auto_create_supplier", True):
        return
    cash_fallback = mappings.get("_mrerp_cash_supplier_fallback", True)
    have = {
        str(r.get("erp_code") or "").strip()
        for r in mappings.get("suppliers") or []
        if isinstance(r, dict)
    }
    pending: Dict[str, Dict[str, str]] = {}
    for h in valid:
        seller = _seller_from_history(h)
        if not seller["code"]:
            # 无卖方身份(现金采购小票)→ 幂等确保现金供应商 เงินสด,不建垃圾码。
            # _supplier_code 对空码直接返 เงินสด。
            if cash_fallback and MRERP_CASH_CUSTOMER not in have:
                pending.setdefault(
                    MRERP_CASH_CUSTOMER,
                    {"code": MRERP_CASH_CUSTOMER, "name": MRERP_CASH_CUSTOMER, "tax_id": ""},
                )
            continue
        if seller["code"] in have:
            continue
        pending.setdefault(seller["code"], seller)
    if pending:
        adapter.create_suppliers(list(pending.values()), mappings)


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
    """商品名 → 确定性商品码(≤15 · 幂等 · md5 仅派生短码非安全 usedforsecurity=False)。"""
    digest = hashlib.md5(name.strip().lower().encode("utf-8"), usedforsecurity=False).hexdigest()
    return ("P" + digest)[:12].upper()


# 费用物料建档结构。453 导入不强制物料类型(服务器接受库存商品 · 2026-07-09 补测证实),
# 建费用/服务型是**会计口径**:费用过账走物料 GL 科目、不该挂库存/销货成本科目。
# type 是 import 认的短标签;8 GL 科目全填同一费用科目。
_EXPENSE_ITEM_TYPE = "บริการ, ค่าใช้จ่าย"
_EXPENSE_ITEM_ACC_KEYS = (
    "acc_rev",
    "acc_ret",
    "acc_dis",
    "acc_pur",
    "acc_purret",
    "acc_purdis",
    "acc_inv",
    "acc_cost",
)


def _expense_cfg(mappings: Dict[str, Any], key: str, default: str) -> str:
    return expense_cfg(mappings, f"_mrerp_expense_item_{key}", default)


def _provision_expense_item(adapter, mappings: Dict[str, Any]) -> None:
    """费用采购(453):只幂等确保通用费用物料存在,**不动 mappings**(含 products)。

    生成器 expense 分支直接用 _mrerp_expense_item_code 取码,不走 _resolve_product_code
    → 注入行名映射没有消费方;且 mappings 在 route_and_upload 各组间共享,注入会把同批
    货品单(67)的同名行解析到费用物料 → 货品票带费用物料推 67 服务器插库异常(跨组污染)。
    建档覆盖同理走浅拷贝;建失败静默返回(推送在 ERP 侧因物料不存在干净失败,不写脏)。
    """
    code = _expense_cfg(mappings, "code", EXPENSE_ITEM_CODE_DEFAULT)
    # 用户在 suppliers/products 映射里配过该码 = 物料已在 ERP,免掉这趟串行 master 导入
    # (镜像货品分支 `if not pending: return` 的短路)。未配则每批幂等确保一次。
    if any(
        str(r.get("erp_code") or "").strip() == code
        for r in mappings.get("products") or []
        if isinstance(r, dict)
    ):
        return
    name = _expense_cfg(mappings, "name", "ค่าใช้จ่าย")
    acc = _expense_cfg(mappings, "acc", "5230-01")
    overrides = {
        "_mrerp_product_type": _EXPENSE_ITEM_TYPE,
        "_mrerp_product_category": _expense_cfg(mappings, "category", "04-SER"),
        **{f"_mrerp_product_{k}": acc for k in _EXPENSE_ITEM_ACC_KEYS},
    }
    adapter.create_products([{"code": code, "name": name, "price": 0}], {**mappings, **overrides})


def provision_products(adapter, valid: List[Dict[str, Any]], mappings: Dict[str, Any]) -> None:
    """明细行对不上已有商品 → 建并注入码;配了通用商品码则映射到它(不逐行新建)。

    `mappings['_mrerp_generic_product']`(向导「通用销售商品码」)= 对不上的行统一映射到该商品,
    推送更快 · 不产生重复商品(不自建)· 见 build_mrerp_adapter。未配 → 逐行 md5 自建(老行为)。
    费用采购(purchase_expense/453)整个另走:通用费用物料 · 见 _provision_expense_item。
    """
    if not isinstance(mappings, dict) or not mappings.get("_mrerp_auto_create_product", True):
        return
    if getattr(getattr(adapter, "module", None), "expense", False):
        _provision_expense_item(adapter, mappings)
        return
    generic = str(mappings.get("_mrerp_generic_product") or "").strip()
    lookup = _build_product_lookup(mappings)
    pending: Dict[str, Dict[str, Any]] = {}
    inject: List[tuple] = []
    for h in valid:
        for item in _iter_items(h):
            name = str(item.get("name") or item.get("description") or "").strip()
            if not name or _resolve_product_code(name, lookup):
                continue
            if generic:
                inject.append((name, generic))  # 映射到通用商品,不新建
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
    products = mappings.setdefault("products", [])
    if generic:
        for name, code in inject:
            products.append({"item_name": name, "erp_code": code})
        return
    if not pending:
        return
    results = adapter.create_products(list(pending.values()), mappings)
    for name, code in inject:
        if results.get(code):
            products.append({"item_name": name, "erp_code": code})
