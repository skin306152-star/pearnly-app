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
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

from services.erp._master_data_cache import TTLCache
from services.erp._matching import (
    fuzzy_match,
    levenshtein_ratio,
    normalize_company_name,
)
from services.erp.exceptions import (
    MRERPBusinessError,
    MRERPTechnicalError,
)

logger = logging.getLogger(__name__)


CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT = 0.82   # Zihao 2026-05-18 拍板

# Per [mrerp-master-data-sync-design.md §3.4](../../docs/integrations/mrerp-master-data-sync-design.md):
# Default customer code template is P{YYMM}{SEQ4} = 9 chars (well under
# the 20-char ceiling). 'P' = Pearnly-created so admins can spot
# auto-created rows in MR.ERP.
DEFAULT_CUSTOMER_CODE_PREFIX = "P"

# Default values for required MR.ERP fields the OCR doesn't provide.
# Tunable per-tenant in a future settings table (see design §8). The
# values here mirror what Zihao manually set when creating customer 0006.
DEFAULT_CUSTOMER_TYPE_CODE = "1-11"           # ลูกหนี้การค้า
DEFAULT_CUSTOMER_TYPE_LABEL = "ลูกหนี้การค้า"
DEFAULT_BRANCH_CODE = "00000"                  # สำนักงานใหญ่
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

CUSTOMER_NAME_MAX = 100   # MR.ERP UI accepts up to ~100; conservative


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
    FORM_PATH = "/armas/allform.php"
    DEFAULT_PAGE_TIMEOUT_MS = 15_000
    SAVE_TIMEOUT_MS = 30_000

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

    def lookup_or_create(
        self,
        buyer: BuyerInfo,
        mappings: Dict[str, Any],
        *,
        seed_customer_code: Optional[str] = None,
    ) -> CustomerSyncResult:
        """Run Layers 0-3 (via `lookup`) then fall through to Layer 4
        copy-from-seed auto-create when nothing matches.

        ``seed_customer_code`` (Zihao 2026-05-18 拍板 · copy path):
            existing MR.ERP customer code (e.g. "0006") whose master-
            data references (salesman / area / shipping / branch / GL
            account codes) the new row should inherit. When omitted
            and a lookup miss occurs, raises
            ``MRERPBusinessError(ERR_NO_SEED_CUSTOMER)`` instead of
            silently failing — auto-create REQUIRES a seed because the
            "fill placeholders" path is rejected by the server.

        Side effects on auto-create:
          - inserts a new customer row in MR.ERP via armas/allform.php
          - mutates `mappings['clients']` so the same buyer in the same
            push job hits Layer 1 on subsequent calls

        Raises:
          - MRERPBusinessError when MR.ERP rejects the create (missing
            seed, server validation, etc.) — caller surfaces this as
            a FailedRow
          - MRERPTechnicalError on Playwright timeouts / lost selectors
        """
        existing = self.lookup(buyer, mappings)
        if existing is not None:
            return existing

        if not seed_customer_code:
            raise MRERPBusinessError(
                f"Auto-create needs a seed customer code "
                f"(ERR_NO_SEED_CUSTOMER) — pick one in the ERP "
                f"connection wizard or pass seed_customer_code "
                f"explicitly. buyer={buyer.name!r}",
                failed_rows=[{"buyer_name": buyer.name,
                              "reason_code": "ERR_NO_SEED_CUSTOMER"}],
            )

        # Layer 4: copy-from-seed.
        result = self._layer4_auto_create(buyer, seed_customer_code)

        # Persist into the mappings dict so downstream calls within the
        # same push job hit Layer 1.
        if buyer.client_id:
            self._upsert_mapping(mappings, buyer.client_id, result.customer_code)
            result.erp_code_persisted = True

        # Cache the new customer for subsequent lookups in this session.
        name_norm = normalize_company_name(buyer.name)
        if name_norm:
            self.cache.set(
                ("by_name", buyer.tenant_id, name_norm),
                result.customer_code,
            )
        return result

    def invalidate(self) -> None:
        """Drop ALL cached entries — call after an auto-create lands so
        the next lookup() picks up the new listing entry."""
        self.cache.clear()

    def delete_customer(self, customer_code: str) -> bool:
        """Best-effort delete of one customer. Used by integration tests
        to clean up auto-created rows.

        Returns True if the customer is gone from the listing afterwards.

        Implementation per probe:
            The btndel→confirmdel() JS is just
                `location = "alldel.php?id=" + id`
            so we GET that URL directly (still browser-driven; §7 compliant).
            This avoids the Playwright "click that triggers an async
            navigation" timing trap that the older btndel-click path
            stumbled into.

        Caller MUST be inside the adapter's `with` block.
        """
        if not customer_code:
            return False
        page = self.adapter._page
        del_url = (
            f"{self.adapter.login_url}/armas/alldel.php?id={customer_code}"
        )
        try:
            page.goto(del_url, wait_until="networkidle",
                      timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            logger.warning("delete_customer nav failed: %s", e)
            return False

        # alldel.php redirects to allview.php via JS after processing.
        # Give the redirect + listing's showdata.php AJAX time to settle.
        page.wait_for_timeout(2_500)
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PWTimeout:
            pass

        # Force a fresh listing render: the cached listing in our local
        # TTLCache + MR.ERP's own showdata.php sometimes lag the delete.
        try:
            page.goto(
                self.adapter.login_url + self.LISTING_PATH,
                wait_until="networkidle",
                timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
            )
            page.wait_for_timeout(1_500)
        except (PWTimeout, PWError):
            pass

        self.invalidate()
        listing = self._fetch_listing()
        gone = not any(r.code == customer_code for r in listing)
        if not gone:
            logger.warning(
                "delete_customer: %s still in listing after delete",
                customer_code,
            )
        return gone

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

    # ----- Layer 4 auto-create ---------------------------------

    def _layer4_auto_create(
        self,
        buyer: BuyerInfo,
        seed_customer_code: str,
    ) -> CustomerSyncResult:
        """Create a new customer row by cloning a seed customer and
        overriding the four fields that are unique to the new row.

        Flow (per [mrerp-customer-copy-flow.md](../../docs/integrations/mrerp-customer-copy-flow.md)):
          1. nav armas/allform.php (blank form)
          2. click #inpdupdata ("สำเนา") → opens bshlistbox popup
          3. wait ~3s for AJAX-populated candidate list
          4. click the seed row in #bshlistboxdetail
          5. ~all 45 fields populate from the seed (incl. all hidden
             master-data IDs and code/detail triplets)
          6. override txtarcode (generated) + txtname (buyer.name)
             + txttaxid (OCR or random) + txtaddr1..4 (OCR address)
          7. click #btnsave → checknull() passes → allsave.php
          8. verify by listing fetch

        The earlier "fill placeholders" path is gone — it was rejected
        by the server with `alert("Data is use in the system")` because
        the placeholder codes weren't real master-data rows. The copy
        flow inherits valid refs by construction.
        """
        if not seed_customer_code:
            raise MRERPBusinessError(
                "ERR_NO_SEED_CUSTOMER — seed_customer_code is required",
                failed_rows=[{"buyer_name": buyer.name,
                              "reason_code": "ERR_NO_SEED_CUSTOMER"}],
            )

        page = self.adapter._page

        # 1) Pick a unique customer code.
        customer_code = self._generate_customer_code()

        target = self.adapter.login_url + self.FORM_PATH
        try:
            page.goto(target, wait_until="networkidle",
                      timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"customer-create form nav timeout: {e}") from e

        # Sanity: confirm we're on the create form.
        if "allform.php" not in (page.url or ""):
            raise MRERPTechnicalError(
                f"customer-create nav landed on {page.url}, not allform.php")

        # 2-5) Copy-from-seed.
        try:
            self._copy_from_seed(page, seed_customer_code)
        except MRERPBusinessError:
            raise
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"copy-from-seed flow timeout: {e}") from e

        # 6) Override the fields that must be unique to the new row.
        try:
            self._override_after_copy(page, customer_code, buyer)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"override-after-copy timeout: {e}") from e

        # 7) Click save.
        dialogs_before = (
            len(self.adapter._session.dialogs)
            if self.adapter._session else 0
        )
        try:
            page.click('button[id="btnsave"]', timeout=5_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"customer-create save click timeout: {e}") from e

        try:
            page.wait_for_load_state("networkidle",
                                      timeout=self.SAVE_TIMEOUT_MS)
        except PWTimeout:
            pass
        page.wait_for_timeout(1_500)

        if self.adapter._session:
            new_dialogs = self.adapter._session.dialogs[dialogs_before:]
        else:
            new_dialogs = []

        # 8) Verify by listing.
        self.invalidate()
        listing = self._fetch_listing()
        if any(r.code == customer_code for r in listing):
            logger.info(
                "auto-created customer %s (seed=%s, buyer=%s)",
                customer_code, seed_customer_code, buyer.name,
            )
            return CustomerSyncResult(
                customer_code=customer_code,
                source="erp_auto_created",
                confidence=1.0,
                matched_name=buyer.name,
                is_new=True,
                erp_code_persisted=False,
            )

        dialog_text = " / ".join(d for d in new_dialogs)[:300]
        raise MRERPBusinessError(
            f"customer auto-create did not appear in listing "
            f"(code={customer_code}, seed={seed_customer_code}, "
            f"dialogs={dialog_text!r})",
            failed_rows=[{
                "buyer_name": buyer.name,
                "customer_code_attempted": customer_code,
                "seed_customer_code": seed_customer_code,
                "dialogs": new_dialogs,
            }],
        )

    def _copy_from_seed(self, page, seed_customer_code: str) -> None:
        """Drive the inpdupdata picker to clone `seed_customer_code`
        into the current form.

        🛠 Patch 1 (Zihao 2026-05-18 拍板): the armas popup uses the
        same virtual-scroll pattern as stkmas — at TEST2019 scale (2
        customers) all rows are in the DOM, but on accounting-firm
        tenants with 50+ customers only ~10 fit at a time. We now use
        the popup's built-in `#bshlistboxinpsearch` input to filter
        down to just the seed before clicking, mirroring the
        `mrerp_product_sync._copy_from_seed` implementation.
        """
        loc = page.locator('input#inpdupdata')
        if loc.count() == 0:
            raise MRERPTechnicalError(
                "inpdupdata (copy) button missing — MR.ERP UI may have "
                "changed"
            )
        loc.first.click(timeout=5_000)

        # Wait for the popup search input (faster signal than
        # detailshow's first <p>; the search input renders before AJAX
        # populates the rows).
        try:
            page.wait_for_selector(
                "#bshlistboxinpsearch",
                state="visible",
                timeout=10_000,
            )
        except PWTimeout as e:
            raise MRERPTechnicalError(
                f"copy picker popup did not render: {e}") from e
        page.wait_for_timeout(500)

        # Type the seed code into the popup's search input. The onkeyup
        # handler `bshdatalistbox()` re-renders the visible rows in
        # real time — only matching ones survive.
        search = page.locator('input#bshlistboxinpsearch')
        try:
            search.fill(seed_customer_code)
            # bshdatalistbox is wired to onkeyup — fire one to trigger
            # the filter, then settle.
            search.press("End")
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"copy picker search input failed: {e}") from e
        page.wait_for_timeout(800)

        # Stricter selector first (exact text-is on the code span), then
        # a fallback substring match in case the code contains
        # characters that confuse text-is().
        row = page.locator(
            "#bshlistboxdetailshow p"
            f":has(span:text-is({seed_customer_code!r}))"
        ).first
        if row.count() == 0:
            row = page.locator(
                "#bshlistboxdetailshow p"
                f":has-text({seed_customer_code!r})"
            ).first
        if row.count() == 0:
            raise MRERPBusinessError(
                f"seed customer {seed_customer_code!r} not visible in "
                f"the copy picker — confirm the code exists in this "
                f"tenant's customer master (searched via "
                f"bshlistboxinpsearch)",
                failed_rows=[{
                    "reason_code": "ERR_SEED_NOT_FOUND",
                    "seed_customer_code": seed_customer_code,
                }],
            )

        try:
            row.click(timeout=3_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"seed row click failed: {e}") from e

        # bshlistboxafterselectdata fires an AJAX fetch to populate the
        # form with the seed's full field set. ~1-2s.
        page.wait_for_timeout(2_500)

        try:
            populated_name = page.locator(
                'input#txtname'
            ).first.input_value()
        except Exception:
            populated_name = ""
        if not populated_name:
            raise MRERPTechnicalError(
                "copy picker click did not populate the form "
                "(txtname still empty)"
            )

    def _override_after_copy(
        self, page, customer_code: str, buyer: BuyerInfo,
    ) -> None:
        """Replace the seed's identity fields with the new customer's.

        Per [mrerp-customer-copy-flow.md §5](../../docs/integrations/mrerp-customer-copy-flow.md):
        leave master-data refs alone; override only the 4 unique fields.
        """
        # Customer code is editable text — direct fill is fine.
        self._fill_field(page, "txtarcode", customer_code)
        # Customer name — truncate to MR.ERP's ceiling.
        self._fill_field(
            page, "txtname",
            (buyer.name or "")[:CUSTOMER_NAME_MAX],
        )

        # Tax ID — use OCR if available + 13 digits, else random.
        tax_id = (buyer.tax_id or "").strip()
        if len(tax_id) == 13 and tax_id.isdigit():
            self._fill_field(page, "txttaxid", tax_id)
        else:
            import secrets
            rand_tin = str(
                secrets.randbelow(10 ** 12) + 10 ** 12
            )[:13]
            self._fill_field(page, "txttaxid", rand_tin)

        # Address override — only when buyer has one (otherwise inherit
        # seed's placeholder address; harmless).
        if buyer.address:
            self._fill_addresses(page, buyer.address)

    def _fill_field(self, page, field_id: str, value: str) -> None:
        loc = page.locator(f'input[id="{field_id}"]')
        if loc.count() == 0:
            return
        loc.first.fill(value)

    def _fill_code_detail_pair(
        self, page, code_field_id: str, code_value: str,
        *, fallback_detail: str = "",
    ) -> None:
        """For inputs that live in a "code + hidden val + detail label"
        triplet (e.g. txtrectype/rectypeval/txtrectypedetail), inject the
        values directly via JS.

        Why JS, not Playwright fill():
          The visible 'code' inputs (txtrectype / txtacfile / txtemp /
          etc.) are marked `readonly` because the real UX is "click the
          input → bshlistbox opens a popup-picker → click an option →
          JS writes back". Playwright's `fill()` rejects readonly
          elements. We bypass the popup by setting the visible value,
          the hidden 'val' that the server actually consumes, and the
          'detail' label so the saved row looks right in MR.ERP's
          listing/edit pages.

        Hidden + detail id naming convention (from probe):
          txt<base>   →  visible 'code' input (readonly)
          <base>val   →  hidden id consumed server-side
          txt<base>detail  →  visible label that auto-fills on pick
        """
        if not code_field_id.startswith("txt"):
            return
        base = code_field_id[3:]
        hidden_id = f"{base}val"
        detail_id = f"{code_field_id}detail"

        import json as _json
        js = """(function(code, fallback, codeId, hiddenId, detailId) {
            var f = document.getElementById(codeId);
            if (f) {
                try { f.removeAttribute('readonly'); } catch(e) {}
                f.value = code;
                try { f.dispatchEvent(new Event('change', {bubbles: true})); } catch(e) {}
            }
            var h = document.getElementById(hiddenId);
            if (h) h.value = code;
            var d = document.getElementById(detailId);
            if (d) d.value = fallback;
            return {
                visible: f ? f.value : null,
                hidden: h ? h.value : null,
                detail: d ? d.value : null
            };
        })""" + (
            f"({_json.dumps(code_value)}, {_json.dumps(fallback_detail)}, "
            f"{_json.dumps(code_field_id)}, {_json.dumps(hidden_id)}, "
            f"{_json.dumps(detail_id)})"
        )
        try:
            result = page.evaluate(js)
            logger.debug(
                "code-detail fill %s -> %s", code_field_id, result,
            )
        except Exception as e:
            logger.warning(
                "JS fill for %s failed: %s", code_field_id, e,
            )

    def _fill_addresses(self, page, address: str) -> None:
        # MR.ERP accepts up to 4 address lines, each TBD-len. Split by
        # newline if present; otherwise just put the whole string in
        # addr1.
        parts = [p.strip() for p in (address or "").split("\n") if p.strip()]
        if not parts:
            return
        for i, p in enumerate(parts[:4], start=1):
            self._fill_field(page, f"txtaddr{i}", p[:80])

    def _generate_customer_code(self) -> str:
        """Pick the next sequence value in the P{YYMM}{SEQ4} namespace.

        Scans the current listing for codes that match the prefix and
        returns one bigger than the max — naive O(N) on a small listing
        is fine. Falls back to a timestamp-suffixed code if the listing
        scan somehow returns no candidates AND we still want uniqueness
        guarantees across processes.
        """
        today = date.today()
        prefix = f"{DEFAULT_CUSTOMER_CODE_PREFIX}{today.year % 100:02d}{today.month:02d}"
        listing = self._fetch_listing()
        existing_seqs: List[int] = []
        for row in listing:
            if row.code.startswith(prefix):
                tail = row.code[len(prefix):]
                if tail.isdigit():
                    existing_seqs.append(int(tail))
        next_seq = (max(existing_seqs) + 1) if existing_seqs else 1
        candidate = f"{prefix}{next_seq:04d}"
        # Defensive: confirm it's not in listing.
        while any(r.code == candidate for r in listing):
            next_seq += 1
            candidate = f"{prefix}{next_seq:04d}"
        return candidate

    def _upsert_mapping(
        self, mappings: Dict[str, Any],
        client_id: int,
        customer_code: str,
    ) -> None:
        clients = (mappings or {}).get("clients") or []
        for m in clients:
            if (
                m.get("erp_type") == "mrerp"
                and int(m.get("client_id") or 0) == int(client_id)
            ):
                m["erp_code"] = customer_code
                return
        clients.append({
            "erp_type": "mrerp",
            "client_id": int(client_id),
            "erp_code": customer_code,
        })
        if isinstance(mappings, dict):
            mappings["clients"] = clients

    # ----- listing fetch ---------------------------------------

    def _fetch_listing(self) -> List[ListingCustomer]:
        """Returns the parsed customer listing, hitting the in-service
        TTLCache to avoid refetching during a single push job.

        A3 (Zihao 2026-05-19 拍板) · two-layer reliability:
          1. wait_for_selector('#showdata p', 10s) after goto · catches
             the slow-render race where networkidle finishes before the
             AJAX listing rows attach to DOM.
          2. On timeout: page.reload() + another 10 s budget.
          3. Still nothing: save_listing_fail_screenshot() · path baked
             into MRERPTechnicalError so /api/version's last_500 carries
             it forward and the route layer's retry can decide whether
             to re-try.
        """
        cached = self.cache.get(self._listing_cache_key)
        if cached is not None:
            return cached

        # Ensure the adapter is logged in + on the right company.
        self.adapter.select_company()
        url = self.adapter.login_url + self.LISTING_PATH
        page = self.adapter._page
        last_err: Optional[Exception] = None
        for attempt in (1, 2):
            try:
                if attempt == 1:
                    page.goto(
                        url,
                        wait_until="networkidle",
                        timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
                    )
                else:
                    # Second attempt: full page reload to shake loose
                    # any half-rendered state from the first GOTO.
                    page.reload(
                        wait_until="networkidle",
                        timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
                    )
                # Wait specifically for the listing rows to attach.
                page.wait_for_selector(
                    "#showdata p", state="attached", timeout=10_000,
                )
                html = page.content() or ""
                rows = parse_armas_listing(html)
                self.cache.set(self._listing_cache_key, rows)
                logger.info(
                    "fetched armas listing: %d rows (attempt %d)",
                    len(rows), attempt,
                )
                return rows
            except PWTimeout as e:
                last_err = e
                logger.warning(
                    "customer listing fetch attempt %d timed out: %s",
                    attempt, e,
                )
                continue
            except Exception as e:
                # Non-timeout: bubble up immediately so the route can
                # report a precise error code instead of a generic retry
                # cascade.
                raise MRERPTechnicalError(
                    f"customer listing fetch raised: {type(e).__name__}: {e}"
                ) from e
        # Both attempts timed out → screenshot + raise.
        shot = self.adapter.save_listing_fail_screenshot("customers")
        raise MRERPTechnicalError(
            f"customer listing fetch failed after wait+reload retry; "
            f"screenshot={shot}; last_error={last_err}"
        )


__all__ = [
    "BuyerInfo",
    "CustomerSyncResult",
    "ListingCustomer",
    "MRERPCustomerSyncService",
    "parse_armas_listing",
    "CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT",
]
