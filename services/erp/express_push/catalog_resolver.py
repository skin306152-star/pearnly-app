# -*- coding: utf-8 -*-
"""商品 / 客户目录解析器 · 判「复用现有 / 拿不准问人 / 新建」(纯函数 · 无 IO · 可单测)。

对着套账既有目录(小助手上报的 reported_products / reported_customers)比对单据行 / 往来方:
- 确定性精确命中优先(客户税号 > 名称骨架相同)→ 复用现有码,并回报命中的是【库存还是非库存】目录;
- 骨架不同但相似度 >= 阈值 → 拿不准,交人裁决(不自作主张建近重复);
- 都不像 → 新建(建到哪个目录由记账画像 posting_mode 定,不在这里判)。

★跨两个目录一起搜(库存 STKTYP=0 + 非库存 3/4/5)是关键:老逻辑只搜非库存目录,故库存里
已有的商品看不见 → 又建一个非库存重复档(泰方报的正是这个)。这里搜全表,命中即复用灭重复。

名称归一复用 summary_import.columns.skeleton(小写 + 剥泰文声调符与空白),故「น้ำแข็ง หลอด」与
「น้ำแข็งหลอด」骨架相同即精确复用,不受声调错位 / 空格影响。相似度用 stdlib difflib(不引第三方;
量级真不够再换 RapidFuzz,见开源选型交接)。返回结构化裁决,显示文案由上层 i18n。
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, List

from services.summary_import.columns import skeleton

# 骨架不同但相似度 >= 此阈值 = 拿不准(问人);低于 = 新建。0.82 经验值,单测钉死行为。
FUZZY_MIN = 0.82


def _match_by_name(name: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """按名称匹配:骨架精确=reuse(带命中 kind)· 高相似=confirm · 否则 new。"""
    sk = skeleton(name)
    if not sk:
        return {"status": "new"}
    best_ratio = 0.0
    best: Dict[str, Any] = {}
    for it in items:
        isk = skeleton(it.get("name") or "")
        if not isk:
            continue
        if isk == sk:
            return {
                "status": "reuse",
                "code": it.get("code"),
                "kind": it.get("kind") or "",
                "reason": "name_exact",
            }
        r = SequenceMatcher(None, sk, isk).ratio()
        if r > best_ratio:
            best_ratio, best = r, it
    if best and best_ratio >= FUZZY_MIN:
        return {
            "status": "confirm",
            "guess": best.get("code"),
            "kind": best.get("kind") or "",
            "sim": round(best_ratio * 100),
        }
    return {"status": "new"}


def resolve_product(name: str, products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """商品名 → 套账现有商品(跨库存+非库存两目录)。

    reuse{code,kind,reason} | confirm{guess,kind,sim} | new。kind=命中主档的 stock|non_stock。
    """
    return _match_by_name(name, products or [])


def resolve_customer(name: str, tax_id: str, customers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """客户 → 税号精确优先(最强锚,名称不同也认),再落名称匹配。"""
    tid = (tax_id or "").strip()
    if tid:
        for c in customers or []:
            if (c.get("tax_id") or "").strip() == tid:
                return {
                    "status": "reuse",
                    "code": c.get("code"),
                    "kind": c.get("kind") or "",
                    "reason": "tax_exact",
                }
    return _match_by_name(name, customers or [])


def build_name_index(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """预建 骨架→主档 精确索引(首现优先)。批量解析用它 O(1) 精确命中,不必每行对全表重算骨架。"""
    idx: Dict[str, Dict[str, Any]] = {}
    for it in items or []:
        sk = skeleton(it.get("name") or "")
        if sk and sk not in idx:
            idx[sk] = it
    return idx


def resolve_product_indexed(
    name: str, index: Dict[str, Dict[str, Any]], products: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """精确命中走预建索引 O(1);未命中才落 resolve_product 的 O(P) 模糊扫(happy path 不跑 difflib)。"""
    sk = skeleton(name)
    hit = index.get(sk) if sk else None
    if hit:
        return {
            "status": "reuse",
            "code": hit.get("code"),
            "kind": hit.get("kind") or "",
            "reason": "name_exact",
        }
    return resolve_product(name, products)
