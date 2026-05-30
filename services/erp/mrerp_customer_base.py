# -*- coding: utf-8 -*-
"""MR.ERP 客户同步 · 共享基座(常量/默认值 + dataclass + listing 解析)· REFACTOR-WA

从 mrerp_customer_sync.py 拆出(纯搬家 · 0 逻辑改)。供主类 + 各 mixin 子模块共享 ·
避免 mixin 子模块循环依赖。dataclass / parse 经主模块 re-export 回 mrerp_customer_sync 命名空间。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date  # noqa: F401
from typing import Any, Dict, List, Literal, Optional

from services.erp._matching import (
    levenshtein_ratio,  # noqa: F401
    normalize_company_name,
)

CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT = 0.82  # Zihao 2026-05-18 拍板

# Per [mrerp-master-data-sync-design.md §3.4](../../docs/integrations/mrerp-master-data-sync-design.md):
# Default customer code template is P{YYMM}{SEQ4} = 9 chars (well under
# the 20-char ceiling). 'P' = Pearnly-created so admins can spot
# auto-created rows in MR.ERP.
DEFAULT_CUSTOMER_CODE_PREFIX = "P"

# Default values for required MR.ERP fields the OCR doesn't provide.
# Tunable per-tenant in a future settings table (see design §8). The
# values here mirror what Zihao manually set when creating customer 0006.
DEFAULT_CUSTOMER_TYPE_CODE = "1-11"  # ลูกหนี้การค้า
DEFAULT_CUSTOMER_TYPE_LABEL = "ลูกหนี้การค้า"
DEFAULT_BRANCH_CODE = "00000"  # สำนักงานใหญ่
DEFAULT_BRANCH_LABEL = "สำนักงานใหญ่"
DEFAULT_COUNTRY = "ไทย"

# checknull() on armas/allform.php demands every "required" cell be
# non-empty. The list below mirrors the JS alert text discovered during
# Phase 3 integration testing (2026-05-18) — Zihao's manual 0006 setup
# only filled 4 fields because the master-data picker prefilled the
# other defaults. Our auto-create skips the picker, so we have to plant
# placeholders for every cell checknull() inspects.
DEFAULT_NUMERIC_TEXT = "0.00"
DEFAULT_PLACEHOLDER = "0000"
# Discovered via bshlistboxdata.php: the txtacfile picker's first valid
# account code on TEST2019 is "1111-01" / เงินสด. Different tenants
# will likely need to override this via tenant_settings — see open
# questions in mrerp-master-data-sync-design.md §9.
TENANT_VALID_ACCOUNT_CODE = "1111-01"
DEFAULT_CREDIT_TERM = "0"
DEFAULT_EXCHANGE_RATE = "1.00"
DEFAULT_CUSTOMER_RANK = "-"

CUSTOMER_NAME_MAX = 100  # MR.ERP UI accepts up to ~100; conservative


@dataclass
class BuyerInfo:
    """Input for customer sync — pulled from OCR + Pearnly client context."""

    name: str
    tenant_id: str = ""
    client_id: int = 0
    tax_id: Optional[str] = None
    address: Optional[str] = None
    branch: Optional[str] = None


@dataclass
class ListingCustomer:
    """One row scraped from armas/allview.php."""

    code: str
    type_name: str
    prefix: str
    name: str
    name_norm: str = ""


@dataclass
class CustomerSyncResult:
    """What lookup / lookup_or_create returns to the adapter."""

    customer_code: str
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "source": self.source,
            "confidence": self.confidence,
            "matched_name": self.matched_name,
            "is_new": self.is_new,
            "erp_code_persisted": self.erp_code_persisted,
        }


# ============================================================
# Listing parsing
# ============================================================

# Per the armas/allview.php structure documented above. The header <p>
# (first one) has literal Thai labels; data rows have actual values.
_ROW_PATTERN = re.compile(
    r"<p\b[^>]*>(?P<body>(?:(?!<p\b)(?!</p>).)*?)</p>",
    re.DOTALL,
)
# Top-level spans only — exclude the nested URA review spans by
# stripping anything after the first 5 top-level <span>s. We capture by
# matching balanced spans iteratively.
_TOP_SPAN_PATTERN = re.compile(
    r"<span\b(?P<attrs>[^>]*)>(?P<inner>.*?)</span>",
    re.DOTALL,
)
_HEADER_LABELS = {"รหัสลูกค้า", "ชื่อประเภทลูกค้า", "คำนำหน้า", "ชื่อลูกค้า", "URA"}


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def _norm_tax(s: Any) -> str:
    """归一化泰国税号:去掉所有非数字 · 仅当结果是 13 位才返回(否则空 = 不可比)。
    P2 税号优先复核用 · 空/非 13 位 → 视为"无可比税号" → 降级名称复核。"""
    if not s:
        return ""
    digits = re.sub(r"\D", "", str(s))
    return digits if len(digits) == 13 else ""


def parse_armas_listing(html: str) -> List[ListingCustomer]:
    """Extract customer rows from an armas/allview.php response.

    Scope: only `<p>` elements inside `<div id="showdata">…</div>`. That
    avoids picking up the footer's status row (which has the same span-
    inside-p shape but contains "Username : / Status : / Company : /
    Database Name :" cells).

    Also skips:
      - the header row (first cell == `รหัสลูกค้า`)
      - rows with fewer than 4 top-level spans
      - rows missing customer_code or customer_name
    """
    scope_match = re.search(
        r'<div\b[^>]*\bid=["\']?showdata["\']?[^>]*>(?P<inner>.*?)</div>',
        html,
        re.DOTALL,
    )
    scope = scope_match.group("inner") if scope_match else html

    customers: List[ListingCustomer] = []
    for m in _ROW_PATTERN.finditer(scope):
        body = m.group("body")
        spans = _extract_top_level_spans(body, limit=5)
        if len(spans) < 4:
            continue
        code = _strip_tags(spans[0]).strip()
        type_name = _strip_tags(spans[1]).strip()
        prefix = _strip_tags(spans[2]).strip()
        name = _strip_tags(spans[3]).strip()
        # Skip header row.
        if code == "รหัสลูกค้า" or type_name == "ชื่อประเภทลูกค้า":
            continue
        if not code or not name:
            continue
        customers.append(
            ListingCustomer(
                code=code,
                type_name=type_name,
                prefix=prefix,
                name=name,
                name_norm=normalize_company_name(name),
            )
        )
    return customers


def _extract_top_level_spans(body: str, *, limit: int = 5) -> List[str]:
    """Yield the contents of the FIRST `limit` top-level <span> elements in
    `body`. Properly handles nested <span>s (URA column has a deep tree)."""
    out: List[str] = []
    i = 0
    n = len(body)
    while i < n and len(out) < limit:
        start = body.find("<span", i)
        if start < 0:
            break
        # Find end of opening tag
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
                # Nested open — skip past its tag
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
