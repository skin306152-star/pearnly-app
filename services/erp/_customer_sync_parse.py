# -*- coding: utf-8 -*-
"""MR.ERP 客户同步 · armas/allview.php listing HTML 解析 leaf。"""

import re
from typing import Any, List

from services.erp._matching import normalize_company_name
from services.erp._customer_sync_models import ListingCustomer

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
