# -*- coding: utf-8 -*-
"""MR.ERP 商品同步 · 常量 / dataclass / HTML 列表解析(leaf · 破巨类循环)。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


from services.erp._matching import (
    normalize_item_name,
)

logger = logging.getLogger(__name__)


PRODUCT_LEVENSHTEIN_THRESHOLD_DEFAULT = 0.90  # Zihao 2026-05-18 拍板
PRODUCT_NAME_MAX = 100  # MR.ERP UI ceiling
DEFAULT_PRODUCT_CODE_PREFIX = "P"  # P{YYMM}{SEQ4}


@dataclass
class ItemInfo:
    """Input for product sync — pulled from OCR `items[].name`."""

    name: str
    tenant_id: str = ""
    unit_code: Optional[str] = None
    # Optional client_id link (for symmetry with BuyerInfo + mappings
    # write-back). When set, the mapping persistence still happens via
    # erp_product_mappings keyed on item_name_norm — not on client_id —
    # because products are tenant-shared, not per-client.
    client_id: int = 0


@dataclass
class ListingProduct:
    """One row scraped from stkmas/allview.php."""

    code: str
    name: str
    category_code: str = ""
    category_name: str = ""
    name_norm: str = ""


@dataclass
class ProductSyncResult:
    """What lookup / lookup_or_create returns to the adapter."""

    product_code: str
    source: Literal[
        "cache_hit",
        "db_mapping",
        "erp_name_match",
        "erp_fuzzy_match",
        "erp_auto_created",
    ]
    confidence: float
    matched_name: Optional[str] = None
    is_new: bool = False
    erp_code_persisted: bool = False
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_code": self.product_code,
            "source": self.source,
            "confidence": self.confidence,
            "matched_name": self.matched_name,
            "is_new": self.is_new,
            "erp_code_persisted": self.erp_code_persisted,
            "warnings": list(self.warnings),
        }


# ============================================================
# Listing parsing — mirrors parse_armas_listing
# ============================================================

_ROW_PATTERN = re.compile(
    r"<p\b[^>]*>(?P<body>(?:(?!<p\b)(?!</p>).)*?)</p>",
    re.DOTALL,
)


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def _extract_top_level_spans(body: str, *, limit: int = 5) -> List[str]:
    """Yield the contents of the FIRST `limit` top-level <span> elements
    in `body`. Properly handles nested <span>s (the URA column has a
    deep tree)."""
    out: List[str] = []
    i = 0
    n = len(body)
    while i < n and len(out) < limit:
        start = body.find("<span", i)
        if start < 0:
            break
        gt = body.find(">", start)
        if gt < 0:
            break
        depth = 1
        j = gt + 1
        while j < n and depth > 0:
            next_open = body.find("<span", j)
            next_close = body.find("</span>", j)
            if next_close < 0:
                break
            if next_open >= 0 and next_open < next_close:
                tag_end = body.find(">", next_open)
                if tag_end < 0:
                    break
                depth += 1
                j = tag_end + 1
            else:
                depth -= 1
                if depth == 0:
                    out.append(body[gt + 1 : next_close])
                    j = next_close + len("</span>")
                else:
                    j = next_close + len("</span>")
        i = j
    return out


def parse_stkmas_listing(html: str) -> List[ListingProduct]:
    """Extract product rows from a stkmas/allview.php response.

    Scope: only `<p>` elements inside `<div id="showdata">…</div>`.
    Skips the header row (first cell == `รหัสสินค้า`).
    """
    scope_match = re.search(
        r'<div\b[^>]*\bid=["\']?showdata["\']?[^>]*>(?P<inner>.*?)</div>',
        html,
        re.DOTALL,
    )
    scope = scope_match.group("inner") if scope_match else html

    products: List[ListingProduct] = []
    for m in _ROW_PATTERN.finditer(scope):
        body = m.group("body")
        spans = _extract_top_level_spans(body, limit=5)
        if len(spans) < 4:
            continue
        code = _strip_tags(spans[0]).strip()
        name = _strip_tags(spans[1]).strip()
        cat_code = _strip_tags(spans[2]).strip()
        cat_name = _strip_tags(spans[3]).strip()
        # Header row guard.
        if code == "รหัสสินค้า" or name == "ชื่อสินค้า":
            continue
        if not code or not name:
            continue
        products.append(
            ListingProduct(
                code=code,
                name=name,
                category_code=cat_code,
                category_name=cat_name,
                name_norm=normalize_item_name(name),
            )
        )
    return products


# ============================================================
# 通用销售商品 · 智能默认建议(P1「开箱即用」· §3.4 step 3)
# ============================================================

# 收入/销售/服务类商品的多语种关键词 · 命中即认为是适合做「通用销售商品」
# 兜底科目的真实商品。覆盖泰(MR.ERP 原生)/英/中/日,大小写无关。
# 沙箱真账号里的典型种子就是 "00-รายได้ส่วนกล..."(รายได้ = 收入)。
_GENERIC_PRODUCT_KEYWORDS = (
    "รายได้",  # th · 收入/营收
    "ขาย",  # th · 销售
    "บริการ",  # th · 服务
    "income",
    "revenue",
    "sales",
    "service",
    "收入",
    "销售",
    "服务",
    "売上",  # ja · 销售
    "収益",  # ja · 收益
    "サービス",  # ja · 服务
)


def suggest_generic_product_code(products: List[Dict[str, Any]]) -> Optional[str]:
    """从商品列表里挑一个最像「销售收入」类的商品码做向导智能默认。

    products = list_mrerp_products 返回的 [{code, name, category_name, ...}].
    策略:先按商品名命中收入类关键词,再按分类名命中;都不中返 None
    (前端让用户自己选,不瞎填)。纯函数 · 无副作用 · 守门可测。
    """
    if not products:
        return None
    kws = _GENERIC_PRODUCT_KEYWORDS

    def _hit(text: str) -> bool:
        low = (text or "").lower()
        return any(kw.lower() in low for kw in kws)

    # 第一优先:商品名命中
    for p in products:
        if p.get("code") and _hit(str(p.get("name") or "")):
            return str(p["code"])
    # 第二优先:分类名命中(名字没写但归在收入类)
    for p in products:
        if p.get("code") and _hit(str(p.get("category_name") or "")):
            return str(p["code"])
    return None
