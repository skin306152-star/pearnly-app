# -*- coding: utf-8 -*-
"""
services/erp/mrerp_customer_sync.py

Customer master-data sync for MR.ERP (P1-B Stage 2 · Phase 2 of 5).

This module implements lookup-only (Layers 0-3); auto-create (Layer 4)
lands in Phase 3 — see `mrerp-master-data-sync-design.md`.

Layers:
    L0  in-process TTLCache (per-service)
    L1  existing `mappings['clients']` row for (client_id, erp_type='mrerp')
        — same shape `mrerp_xlsx_generator.lookup_customer_code` consumes
    L2  exact normalized-name match in MR.ERP customer listing
    L3  Levenshtein-ratio fuzzy match in MR.ERP customer listing
        (threshold 0.82, Zihao 2026-05-18 拍板; tightened from the 0.88
        design recommendation to catch more typo variants)

The MR.ERP listing (`armas/allview.php`) returns:
    <p>
      <span>customer_code</span>
      <span>customer_type_name</span>    e.g. ลูกหนี้การค้า
      <span>prefix</span>                 e.g. บริษัท / blank
      <span>customer_name</span>
      <span>URA review history</span>
    </p>

Note the listing does NOT expose tax_id; we cannot do "exact tax_id
match" purely from the listing. If/when a future call has tax_id in
hand, the verification would require clicking into each candidate's
detail page (`allform.php?id=N&status=view`). Out of scope for this
phase — the design doc's §3.3 "Layer 2 tax_id exact" is parked.

Public API:
    @dataclass class BuyerInfo                 — input shape
    @dataclass class CustomerSyncResult        — return shape
    class MRERPCustomerSyncService:
        lookup(buyer, mappings) -> Optional[CustomerSyncResult]
        # Phase 3 will add: lookup_or_create(buyer, mappings)
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from playwright.sync_api import TimeoutError as PWTimeout

from services.erp._master_data_cache import TTLCache
from services.erp._matching import (
    fuzzy_match,
    levenshtein_ratio,
    normalize_company_name,
)
from services.erp.exceptions import MRERPTechnicalError

logger = logging.getLogger(__name__)


CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT = 0.82   # Zihao 2026-05-18 拍板


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
    r'<p\b[^>]*>(?P<body>(?:(?!<p\b)(?!</p>).)*?)</p>',
    re.DOTALL,
)
# Top-level spans only — exclude the nested URA review spans by
# stripping anything after the first 5 top-level <span>s. We capture by
# matching balanced spans iteratively.
_TOP_SPAN_PATTERN = re.compile(
    r'<span\b(?P<attrs>[^>]*)>(?P<inner>.*?)</span>',
    re.DOTALL,
)
_HEADER_LABELS = {"รหัสลูกค้า", "ชื่อประเภทลูกค้า", "คำนำหน้า",
                  "ชื่อลูกค้า", "URA"}


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


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
        customers.append(ListingCustomer(
            code=code, type_name=type_name, prefix=prefix, name=name,
            name_norm=normalize_company_name(name),
        ))
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
                    out.append(body[gt + 1:next_close])
                    j = next_close + len("</span>")
                else:
                    j = next_close + len("</span>")
        i = j
    return out


# ============================================================
# Service
# ============================================================

class MRERPCustomerSyncService:
    """Lookup helper for customer master data.

    Construct with an active MRERPAdapter (the service uses its
    BrowserSession / page; it does NOT create its own browser).
    """

    LISTING_PATH = "/armas/allview.php"
    DEFAULT_PAGE_TIMEOUT_MS = 15_000

    def __init__(
        self,
        adapter,
        *,
        customer_threshold: float = CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT,
        cache: Optional[TTLCache] = None,
    ):
        self.adapter = adapter
        self.customer_threshold = float(customer_threshold)
        self.cache = cache or TTLCache(max_size=1024, ttl_seconds=300.0)
        # Cached full listing per session — refreshes when the cache
        # entry expires. Listings are small enough (we saw ~4 KB / 2
        # rows) that re-fetching is cheap.
        self._listing_cache_key = "__armas_listing__"

    # ----- public API ------------------------------------------

    def lookup(
        self,
        buyer: BuyerInfo,
        mappings: Dict[str, Any],
    ) -> Optional[CustomerSyncResult]:
        """Try Layers 0-3. Returns None if no match passes the threshold.

        Side effect: hits L0 caches as it goes. Does NOT mutate `mappings`
        (Phase 3's lookup_or_create will).
        """
        if not buyer or not buyer.name:
            return None

        # L0 · cache by (tenant_id, normalized name).
        name_norm = normalize_company_name(buyer.name)
        cache_key = ("by_name", buyer.tenant_id, name_norm)
        cached_code = self.cache.get(cache_key) if name_norm else None
        if cached_code:
            logger.debug("customer cache hit: %s -> %s",
                         name_norm, cached_code)
            return CustomerSyncResult(
                customer_code=cached_code,
                source="cache_hit",
                confidence=1.0,
                matched_name=buyer.name,
            )

        # L1 · existing mapping for this client_id.
        l1 = self._layer1_db_mapping(buyer, mappings)
        if l1 is not None:
            self.cache.set(cache_key, l1.customer_code)
            return l1

        # L2/L3 · scan the live listing.
        listing = self._fetch_listing()

        l2 = self._layer2_exact_name(name_norm, listing)
        if l2 is not None:
            self.cache.set(cache_key, l2.customer_code)
            return l2

        l3 = self._layer3_fuzzy_name(name_norm, listing)
        if l3 is not None:
            self.cache.set(cache_key, l3.customer_code)
            return l3

        return None

    def invalidate(self) -> None:
        """Drop ALL cached entries — call after an auto-create lands so
        the next lookup() picks up the new listing entry."""
        self.cache.clear()

    # ----- layers ----------------------------------------------

    def _layer1_db_mapping(
        self,
        buyer: BuyerInfo,
        mappings: Dict[str, Any],
    ) -> Optional[CustomerSyncResult]:
        if not buyer.client_id:
            return None
        for m in (mappings or {}).get("clients") or []:
            if m.get("erp_type") != "mrerp":
                continue
            try:
                if int(m.get("client_id") or 0) != int(buyer.client_id):
                    continue
            except (TypeError, ValueError):
                continue
            code = str(m.get("erp_code") or "").strip()
            if code:
                return CustomerSyncResult(
                    customer_code=code,
                    source="db_mapping",
                    confidence=1.0,
                    matched_name=buyer.name,
                )
        return None

    def _layer2_exact_name(
        self,
        name_norm: str,
        listing: List[ListingCustomer],
    ) -> Optional[CustomerSyncResult]:
        if not name_norm:
            return None
        for row in listing:
            if row.name_norm and row.name_norm == name_norm:
                return CustomerSyncResult(
                    customer_code=row.code,
                    source="erp_name_match",
                    confidence=1.0,
                    matched_name=row.name,
                )
        return None

    def _layer3_fuzzy_name(
        self,
        name_norm: str,
        listing: List[ListingCustomer],
    ) -> Optional[CustomerSyncResult]:
        if not name_norm:
            return None
        # Build the candidate list. We score against the NORMALIZED form
        # so legal-suffix variants don't hurt the ratio.
        best_row: Optional[ListingCustomer] = None
        best_ratio = 0.0
        for row in listing:
            if not row.name_norm:
                continue
            r = levenshtein_ratio(name_norm, row.name_norm)
            if r > best_ratio:
                best_ratio = r
                best_row = row
        if best_row is None or best_ratio < self.customer_threshold:
            return None
        return CustomerSyncResult(
            customer_code=best_row.code,
            source="erp_fuzzy_match",
            confidence=best_ratio,
            matched_name=best_row.name,
        )

    # ----- listing fetch ---------------------------------------

    def _fetch_listing(self) -> List[ListingCustomer]:
        """Returns the parsed customer listing, hitting the in-service
        TTLCache to avoid refetching during a single push job."""
        cached = self.cache.get(self._listing_cache_key)
        if cached is not None:
            return cached

        # Ensure the adapter is logged in + on the right company.
        self.adapter.select_company()
        url = self.adapter.login_url + self.LISTING_PATH
        page = self.adapter._page
        try:
            page.goto(
                url,
                wait_until="networkidle",
                timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
            )
            html = page.content() or ""
        except PWTimeout as e:
            raise MRERPTechnicalError(
                f"customer listing fetch timeout: {e}") from e

        rows = parse_armas_listing(html)
        # Cache for the rest of the session.
        self.cache.set(self._listing_cache_key, rows)
        logger.info("fetched armas listing: %d rows", len(rows))
        return rows


__all__ = [
    "BuyerInfo",
    "CustomerSyncResult",
    "ListingCustomer",
    "MRERPCustomerSyncService",
    "parse_armas_listing",
    "CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT",
]
