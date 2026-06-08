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
from typing import Optional

from services.erp._master_data_cache import TTLCache
from services.erp._customer_sync_const import (  # noqa: F401  public re-export
    CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT,
)
from services.erp._customer_sync_models import (  # noqa: F401  public re-export
    BuyerInfo,
    ListingCustomer,
    CustomerSyncResult,
)
from services.erp._customer_sync_parse import (  # noqa: F401  public re-export
    _norm_tax,
    _strip_tags,
    parse_armas_listing,
)
from services.erp._customer_sync_resolve import CustomerResolveMixin
from services.erp._customer_sync_create import CustomerCreateMixin
from services.erp._customer_sync_fetch import CustomerFetchMixin

logger = logging.getLogger(__name__)


class MRERPCustomerSyncService(
    CustomerResolveMixin,
    CustomerCreateMixin,
    CustomerFetchMixin,
):
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
        # 自动挑的默认种子客户码缓存(没配 seed 时自动建用 · 见 _resolve_default_seed)
        self._default_seed_cache: Optional[str] = None

    # ----- cache -----
    def invalidate(self) -> None:
        """Drop ALL cached entries — call after an auto-create lands so
        the next lookup() picks up the new listing entry."""
        self.cache.clear()


__all__ = [
    "BuyerInfo",
    "CustomerSyncResult",
    "ListingCustomer",
    "MRERPCustomerSyncService",
    "parse_armas_listing",
    "CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT",
]
