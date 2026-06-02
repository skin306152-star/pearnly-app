# -*- coding: utf-8 -*-
"""
services/erp/mrerp_product_sync.py · MR.ERP 商品(stkmas)主数据同步(facade)。

巨类 MRERPProductSyncService 按职责拆 3 Mixin(lookup/create/listing),本模块多继承
组装 + 保留 __init__/invalidate/delete_product。常量/dataclass/解析函数在 mrerp_product_base。
Layer cascade L0 cache → L1 db → L2 exact → L3 fuzzy → L4 copy-from-seed auto-create。
"""

from __future__ import annotations

from typing import Optional

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

from services.erp._master_data_cache import TTLCache


from services.erp.mrerp_product_base import (  # noqa: F401 · re-export(__all__ + 外部 import 契约)
    PRODUCT_LEVENSHTEIN_THRESHOLD_DEFAULT,
    PRODUCT_NAME_MAX,
    DEFAULT_PRODUCT_CODE_PREFIX,
    ItemInfo,
    ListingProduct,
    ProductSyncResult,
    parse_stkmas_listing,
    suggest_generic_product_code,
    logger,
)
from services.erp.mrerp_product_lookup import ProductLookupMixin
from services.erp.mrerp_product_create import ProductCreateMixin
from services.erp.mrerp_product_listing import ProductListingMixin


class MRERPProductSyncService(ProductLookupMixin, ProductCreateMixin, ProductListingMixin):
    """Lookup + auto-create helper for product master data.

    Construct with an active MRERPAdapter (the service uses its
    BrowserSession / page; it does NOT create its own browser).
    """

    LISTING_PATH = "/stkmas/allview.php"
    FORM_PATH = "/stkmas/allform.php"
    DELETE_PATH = "/stkmas/alldel.php"
    DEFAULT_PAGE_TIMEOUT_MS = 15_000
    SAVE_TIMEOUT_MS = 30_000

    def __init__(
        self,
        adapter,
        *,
        product_threshold: float = PRODUCT_LEVENSHTEIN_THRESHOLD_DEFAULT,
        cache: Optional[TTLCache] = None,
    ):
        self.adapter = adapter
        self.product_threshold = float(product_threshold)
        self.cache = cache or TTLCache(max_size=1024, ttl_seconds=300.0)
        self._listing_cache_key = "__stkmas_listing__"

    def invalidate(self) -> None:
        self.cache.clear()

    def delete_product(self, product_code: str) -> bool:
        """Best-effort delete · same alldel.php pattern as customers.
        Note: test01 returns "Delete Success" but doesn't actually
        delete (documented limitation — admin permission required).
        """
        if not product_code:
            return False
        page = self.adapter._page
        del_url = f"{self.adapter.login_url}{self.DELETE_PATH}" f"?id={product_code}"
        try:
            page.goto(del_url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            logger.warning("delete_product nav failed: %s", e)
            return False
        page.wait_for_timeout(2_500)
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PWTimeout:
            pass
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
        gone = not any(r.code == product_code for r in listing)
        if not gone:
            logger.warning(
                "delete_product: %s still in listing after delete",
                product_code,
            )
        return gone


__all__ = [
    "ItemInfo",
    "ListingProduct",
    "ProductSyncResult",
    "MRERPProductSyncService",
    "parse_stkmas_listing",
    "PRODUCT_LEVENSHTEIN_THRESHOLD_DEFAULT",
]
