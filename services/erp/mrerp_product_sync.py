# -*- coding: utf-8 -*-
"""
services/erp/mrerp_product_sync.py

Product (stkmas) master-data sync for MR.ERP.

Mirrors the Customer Sync service (mrerp_customer_sync.py) layer-for-
layer, with two differences forced by the OCR / MR.ERP shape:

1. No tax_id signal — product names are the only OCR field we have.
   Layer 2 becomes "exact normalized-name match" (no TIN-exact tier).
2. Layer 4 auto-create overrides more fields than the customer
   equivalent: stkcode / stkname / stkapcode / stkapname / stkarcode /
   stkarname all get rewritten. Unit, price, account refs, BOM stay
   inherited from seed.

Zihao 2026-05-18 拍板 answers (master-data-sync-design §4.5):
    Q1 Sales price        → Copy from seed (seed's txtsprice inherits)
    Q2 Multi-seed         → v1 single seed per tenant (single
                             endpoint.config.seed_product_code)
    Q3 Unit OCR mismatch  → ERR_PRODUCT_UNIT_NOT_FOUND (don't silently
                             override the seed's unit; raise so the
                             user sees the issue)
    Q4 Name ≥ 100 chars   → truncate + WARN_PRODUCT_NAME_TRUNCATED
                             (non-blocking; result still saves)
    Q5 Cleanup permission → same alldel.php limitation as customers
                             (test01 returns success but doesn't
                             actually delete); documented + tests
                             treat cleanup as best-effort.

Layer cascade:
    L0  in-process TTLCache (per-service)
    L1  existing `mappings['products']` row for (item_name_norm,
        erp_type='mrerp')
    L2  exact normalized-name match in stkmas/allview.php listing
    L3  Levenshtein fuzzy (threshold 0.90 — Zihao 拍板)
    L4  Copy-from-seed auto-create (drives inpdupdata picker, same
        as Customer)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

from services.erp._master_data_cache import TTLCache
from services.erp._matching import (
    levenshtein_ratio,
    normalize_item_name,
)
from services.erp.exceptions import (
    MRERPBusinessError,
    MRERPTechnicalError,
)
from services.erp._listing_paginate import fetch_all_listing_pages

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
# The service
# ============================================================


class MRERPProductSyncService:
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

    # ----- public API ------------------------------------------

    def lookup(
        self,
        item: ItemInfo,
        mappings: Dict[str, Any],
    ) -> Optional[ProductSyncResult]:
        """Try Layers 0-3. Returns None if no match passes the threshold."""
        if not item or not item.name:
            return None

        name_norm = normalize_item_name(item.name)
        cache_key = ("by_item_name", item.tenant_id, name_norm)
        cached_code = self.cache.get(cache_key) if name_norm else None
        if cached_code:
            return ProductSyncResult(
                product_code=cached_code,
                source="cache_hit",
                confidence=1.0,
                matched_name=item.name,
            )

        l1 = self._layer1_db_mapping(item, mappings)
        if l1 is not None:
            self.cache.set(cache_key, l1.product_code)
            return l1

        # 最终冲刺 (Zihao 2026-05-19 拍板 · v118.34.27) · listing fetch 在 TEST2019
        # 30s × 3 还炸 · 不让它阻断 lookup. fail-soft: 拿不到 listing 就当成 L2/L3
        # 无 match · 让 lookup_or_create 走 L4 auto-create (创建不依赖 listing).
        try:
            listing = self._fetch_listing()
        except MRERPTechnicalError as e:
            logger.warning(
                "product _fetch_listing failed in lookup · skipping L2/L3 · "
                "fall through to None (caller will go L4 auto-create): %s",
                e,
            )
            return None

        l2 = self._layer2_exact_name(name_norm, listing)
        if l2 is not None:
            self.cache.set(cache_key, l2.product_code)
            return l2

        l3 = self._layer3_fuzzy_name(name_norm, listing)
        if l3 is not None:
            self.cache.set(cache_key, l3.product_code)
            return l3

        return None

    def lookup_or_create(
        self,
        item: ItemInfo,
        mappings: Dict[str, Any],
        *,
        seed_product_code: Optional[str] = None,
    ) -> ProductSyncResult:
        """Layers 0-3 first, then Layer 4 copy-from-seed auto-create
        when nothing matches.

        Raises:
          MRERPBusinessError(ERR_NO_SEED_PRODUCT) when lookup misses
          and no seed is provided. Auto-create REQUIRES a seed (same
          rule as Customer Sync — without it, the placeholder-fill
          path would be rejected by allsave.php).
        """
        existing = self.lookup(item, mappings)
        if existing is not None:
            return existing

        if not seed_product_code:
            raise MRERPBusinessError(
                f"Auto-create needs a seed product code "
                f"(ERR_NO_SEED_PRODUCT) — pick one in the ERP "
                f"connection wizard or pass seed_product_code "
                f"explicitly. item={item.name!r}",
                failed_rows=[
                    {
                        "item_name": item.name,
                        "reason_code": "ERR_NO_SEED_PRODUCT",
                    }
                ],
            )

        result = self._layer4_auto_create(item, seed_product_code)

        # Persist into the mappings dict so subsequent calls within the
        # same push job hit Layer 1.
        self._upsert_mapping(mappings, item, result.product_code)
        result.erp_code_persisted = True

        name_norm = normalize_item_name(item.name)
        if name_norm:
            self.cache.set(
                ("by_item_name", item.tenant_id, name_norm),
                result.product_code,
            )
        return result

    def verify_resolved_code(
        self,
        product_code: str,
        item_name: str,
    ) -> str:
        """Fail-safe(Zihao 2026-05-26 拍板 · P1):复核一个**已解析出**的
        product_code 在 MR.ERP 里的真实商品名是否跟发票商品行匹配。

        背景:推送时 product_code 可能来自 stale db_mapping(实测:16 条不同
        商品全映射到占位码 123)· 或 generator 找不到映射时 fallback '123' →
        所有商品行静默记到占位商品上。本方法把"静默错记"变"响亮失败"。

        Returns:
            匹配时返回 MR.ERP 里的真实商品名。

        Raises:
            MRERPBusinessError(ERR_PRODUCT_NAME_MISMATCH)
                反查到该码但真名 vs OCR 商品名相似度 < 阈值(占位 123 必中)。
            MRERPTechnicalError(ERR_PRODUCT_VERIFY_UNAVAILABLE)
                无法向 MR.ERP 确认(search/listing 技术异常,或搜不到该码)。
        """
        code = (product_code or "").strip()
        name = (item_name or "").strip()
        if not code or not name:
            raise MRERPTechnicalError(
                f"ERR_PRODUCT_VERIFY_UNAVAILABLE — cannot verify "
                f"(code={code!r}, item={name!r} · one is empty)"
            )

        # 2026-05-26 修:复核搜索加 1 次重试 · 大目录/服务端抖动下单次易超时 →
        # 误判 ERR_PRODUCT_VERIFY_UNAVAILABLE 把能推的发票挡下(生产实测)。
        import time as _time

        listing = None
        last_err: Optional[Exception] = None
        for attempt in (1, 2):
            try:
                listing = self._search_listing(code)
                break
            except MRERPTechnicalError as e:
                last_err = e
                if attempt < 2:
                    _time.sleep(2)
        if listing is None:
            raise MRERPTechnicalError(
                f"ERR_PRODUCT_VERIFY_UNAVAILABLE — MR.ERP listing lookup "
                f"failed for product_code {code!r} after retry: {last_err}"
            ) from last_err

        row = next((r for r in listing if r.code == code), None)
        if row is None:
            raise MRERPTechnicalError(
                f"ERR_PRODUCT_VERIFY_UNAVAILABLE — product_code {code!r} "
                f"not found in MR.ERP listing (cannot confirm it matches "
                f"item {name!r})"
            )

        item_norm = normalize_item_name(name)
        erp_norm = row.name_norm or normalize_item_name(row.name)
        ratio = levenshtein_ratio(item_norm, erp_norm) if (item_norm and erp_norm) else 0.0
        if ratio >= self.product_threshold:
            return row.name

        raise MRERPBusinessError(
            f"ERR_PRODUCT_NAME_MISMATCH — resolved product_code {code!r} "
            f"maps to MR.ERP product {row.name!r} but the invoice line is "
            f"{name!r} (name ratio={ratio:.2f} < {self.product_threshold})",
            failed_rows=[
                {
                    "reason_code": "ERR_PRODUCT_NAME_MISMATCH",
                    "product_code": code,
                    "erp_product_name": row.name,
                    "item_name": name,
                    "name_ratio": round(ratio, 3),
                }
            ],
        )

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

    # ----- layers ----------------------------------------------

    def _layer1_db_mapping(
        self,
        item: ItemInfo,
        mappings: Dict[str, Any],
    ) -> Optional[ProductSyncResult]:
        """Match against `mappings['products']` keyed by item_name_norm
        + erp_type='mrerp'. Matches the schema of `erp_product_mappings`
        in db.py."""
        name_norm = normalize_item_name(item.name)
        if not name_norm:
            return None
        for m in (mappings or {}).get("products") or []:
            if m.get("erp_type") != "mrerp":
                continue
            cand_norm = m.get("item_name_norm") or normalize_item_name(m.get("item_name", ""))
            if cand_norm == name_norm:
                code = str(m.get("erp_code") or "").strip()
                if code:
                    return ProductSyncResult(
                        product_code=code,
                        source="db_mapping",
                        confidence=1.0,
                        matched_name=item.name,
                    )
        return None

    def _layer2_exact_name(
        self,
        name_norm: str,
        listing: List[ListingProduct],
    ) -> Optional[ProductSyncResult]:
        if not name_norm:
            return None
        for row in listing:
            if row.name_norm and row.name_norm == name_norm:
                return ProductSyncResult(
                    product_code=row.code,
                    source="erp_name_match",
                    confidence=1.0,
                    matched_name=row.name,
                )
        return None

    def _layer3_fuzzy_name(
        self,
        name_norm: str,
        listing: List[ListingProduct],
    ) -> Optional[ProductSyncResult]:
        if not name_norm:
            return None
        best_row: Optional[ListingProduct] = None
        best_ratio = 0.0
        for row in listing:
            if not row.name_norm:
                continue
            r = levenshtein_ratio(name_norm, row.name_norm)
            if r > best_ratio:
                best_ratio = r
                best_row = row
        if best_row is None or best_ratio < self.product_threshold:
            return None
        return ProductSyncResult(
            product_code=best_row.code,
            source="erp_fuzzy_match",
            confidence=best_ratio,
            matched_name=best_row.name,
        )

    # ----- Layer 4 auto-create ---------------------------------

    def _layer4_auto_create(
        self,
        item: ItemInfo,
        seed_product_code: str,
    ) -> ProductSyncResult:
        """Clone a seed product via the inpdupdata picker, then
        override the 6 fields that must be unique to the new row:
            txtstkcode / txtstkname /
            txtstkapcode / txtstkapname /
            txtstkarcode / txtstkarname

        All other fields (units, prices, GL account refs, BOM, etc.)
        inherit from the seed by construction.
        """
        if not seed_product_code:
            raise MRERPBusinessError(
                "ERR_NO_SEED_PRODUCT — seed_product_code is required",
                failed_rows=[
                    {
                        "item_name": item.name,
                        "reason_code": "ERR_NO_SEED_PRODUCT",
                    }
                ],
            )

        page = self.adapter._page
        product_code = self._generate_product_code()
        warnings: List[str] = []

        # Truncate-if-too-long with a non-blocking WARN (Zihao Q4).
        raw_name = item.name or ""
        truncated_name = raw_name[:PRODUCT_NAME_MAX]
        if len(raw_name) > PRODUCT_NAME_MAX:
            warnings.append("WARN_PRODUCT_NAME_TRUNCATED")
            logger.info(
                "product name truncated %d→%d chars: %r",
                len(raw_name),
                PRODUCT_NAME_MAX,
                raw_name[:60],
            )

        target = self.adapter.login_url + self.FORM_PATH
        try:
            page.goto(target, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"product-create form nav timeout: {e}") from e

        # Bug 8 fix (Zihao 2026-05-19 拍板 · v118.34.23) · MR.ERP PHP session
        # 偶尔在 customer-sync 跑完后 · 进到 stkmas 模块时被服务端无声 invalidate.
        # 表现: page.url 落在 /login/login.php · 不是 /stkmas/allform.php.
        # 修: detect 这种 bounce · 尝试 re-login + select_company + 再 goto 一次.
        # 仍失败才抛 ERR_TECHNICAL · 给用户清晰路径(刷新重试 / 等几分钟).
        landed_url = page.url or ""
        if "/login/login.php" in landed_url:
            logger.warning("[product-create] nav bounced to login.php · attempt re-login + retry")
            warnings.append("WARN_SESSION_REFRESHED")
            try:
                # Force re-login by toggling _logged_in flag · adapter.login()
                # is idempotent · _company_selected also clears.
                self.adapter._logged_in = False
                self.adapter._company_selected = False
                self.adapter.login()
                self.adapter.select_company()
                page.goto(target, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            except Exception as e:
                raise MRERPTechnicalError(
                    f"product-create session re-login failed: {type(e).__name__}: {e}"
                ) from e
            landed_url = page.url or ""

        if "allform.php" not in landed_url:
            raise MRERPTechnicalError(
                f"product-create nav landed on {landed_url}, not allform.php "
                f"(session refresh did not recover)"
            )

        try:
            self._copy_from_seed(page, seed_product_code)
        except MRERPBusinessError:
            raise
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"product copy-from-seed timeout: {e}") from e

        try:
            self._override_after_copy(page, product_code, truncated_name)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"product override-after-copy timeout: {e}") from e

        # Zihao Q3: OCR unit mismatch — if item.unit_code is set AND
        # differs from the seed's unit, raise ERR_PRODUCT_UNIT_NOT_FOUND
        # rather than silently overriding.
        if item.unit_code:
            try:
                inherited_unit = page.evaluate(
                    "document.getElementById('txtunit_usell')?.value || ''"
                )
                if (
                    inherited_unit
                    and item.unit_code.strip()
                    and item.unit_code.strip() != inherited_unit.strip()
                ):
                    raise MRERPBusinessError(
                        f"ERR_PRODUCT_UNIT_NOT_FOUND — OCR unit "
                        f"{item.unit_code!r} differs from seed's "
                        f"{inherited_unit!r}; either pick a seed with "
                        f"the right unit or strip the OCR unit hint",
                        failed_rows=[
                            {
                                "item_name": item.name,
                                "reason_code": "ERR_PRODUCT_UNIT_NOT_FOUND",
                                "ocr_unit": item.unit_code,
                                "seed_unit": inherited_unit,
                            }
                        ],
                    )
            except MRERPBusinessError:
                raise
            except Exception:
                pass

        dialogs_before = len(self.adapter._session.dialogs) if self.adapter._session else 0
        try:
            page.click('button[id="btnsave"]', timeout=5_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"product save click timeout: {e}") from e

        try:
            page.wait_for_load_state("networkidle", timeout=self.SAVE_TIMEOUT_MS)
        except PWTimeout:
            pass
        page.wait_for_timeout(1_500)

        if self.adapter._session:
            new_dialogs = self.adapter._session.dialogs[dialogs_before:]
        else:
            new_dialogs = []

        # Document the seed-inherited price as a non-blocking warning
        # so the caller can surface "review the price" to the user.
        warnings.append("WARN_PRODUCT_PRICE_INHERITED_FROM_SEED")

        self.invalidate()
        listing = self._fetch_listing()
        if any(r.code == product_code for r in listing):
            # P3 闭环反查(Zihao 2026-05-26 section 五):建完复核新码对应商品名 ==
            # 发票商品行。名不符(BusinessError)→ 抛(建出来的不是这个商品 · 不推)。
            # 反查不可用(TechnicalError)→ 降级:刚写的就是该商品名 · 可信 · 仅 log。
            try:
                self.verify_resolved_code(product_code, item.name)
            except MRERPBusinessError:
                raise
            except MRERPTechnicalError as e:
                logger.warning(
                    "product auto-create post-verify unavailable for %s (trusting "
                    "just-written name): %s",
                    product_code,
                    e,
                )
            logger.info(
                "auto-created product %s (seed=%s, name=%s)",
                product_code,
                seed_product_code,
                item.name[:60],
            )
            return ProductSyncResult(
                product_code=product_code,
                source="erp_auto_created",
                confidence=1.0,
                matched_name=item.name,
                is_new=True,
                erp_code_persisted=False,
                warnings=warnings,
            )

        dialog_text = " / ".join(d for d in new_dialogs)[:300]
        raise MRERPBusinessError(
            f"product auto-create did not appear in listing "
            f"(code={product_code}, seed={seed_product_code}, "
            f"dialogs={dialog_text!r})",
            failed_rows=[
                {
                    "item_name": item.name,
                    "product_code_attempted": product_code,
                    "seed_product_code": seed_product_code,
                    "dialogs": new_dialogs,
                }
            ],
        )

    def _copy_from_seed(self, page, seed_product_code: str) -> None:
        """Drive the inpdupdata picker to clone `seed_product_code`.

        stkmas listings are larger than armas (TEST2019 has 73 products
        vs 2 customers), so the popup virtualises rows — only ~10 are
        in the DOM at a time. We use the popup's built-in
        `#bshlistboxinpsearch` field to filter down to just the seed
        before clicking, which works regardless of tenant size.
        """
        loc = page.locator("input#inpdupdata")
        if loc.count() == 0:
            raise MRERPTechnicalError(
                "stkmas inpdupdata (copy) button missing — MR.ERP UI " "may have changed"
            )
        loc.first.click(timeout=5_000)
        try:
            page.wait_for_selector(
                "#bshlistboxinpsearch",
                state="visible",
                timeout=10_000,
            )
        except PWTimeout as e:
            raise MRERPTechnicalError(f"product copy picker popup did not render: {e}") from e
        page.wait_for_timeout(500)

        # Type the seed code into the popup's search input. The onkeyup
        # handler `bshdatalistbox()` re-filters the visible rows in
        # real time.
        search = page.locator("input#bshlistboxinpsearch")
        try:
            search.fill(seed_product_code)
            # bshdatalistbox is wired to onkeyup — fire one to trigger
            # the filter, then settle.
            search.press("End")
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"product copy picker search input failed: {e}") from e
        page.wait_for_timeout(800)

        row = page.locator(
            "#bshlistboxdetailshow p" f":has(span:text-is({seed_product_code!r}))"
        ).first
        # Fallback selector: less strict (substring match) in case the
        # code contains characters that confuse text-is().
        if row.count() == 0:
            row = page.locator("#bshlistboxdetailshow p" f":has-text({seed_product_code!r})").first
        if row.count() == 0:
            raise MRERPBusinessError(
                f"ERR_SEED_PRODUCT_NOT_FOUND — seed product "
                f"{seed_product_code!r} not visible in the copy picker "
                f"(searched via bshlistboxinpsearch)",
                failed_rows=[
                    {
                        "reason_code": "ERR_SEED_PRODUCT_NOT_FOUND",
                        "seed_product_code": seed_product_code,
                    }
                ],
            )
        try:
            row.click(timeout=3_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"product seed row click failed: {e}") from e
        page.wait_for_timeout(2_500)

        try:
            populated_name = page.locator("input#txtstkname").first.input_value()
        except Exception:
            populated_name = ""
        if not populated_name:
            raise MRERPTechnicalError(
                "product copy picker click did not populate " "(txtstkname still empty)"
            )

    def _override_after_copy(
        self,
        page,
        product_code: str,
        item_name: str,
    ) -> None:
        """Replace seed identity fields with the new product's. Per
        mrerp-product-form-fields.md §4.4: 6 fields override, all
        master-data refs (units / accounts / category) inherit from seed.
        """
        self._fill_field(page, "txtstkcode", product_code)
        self._fill_field(page, "txtstkname", item_name)
        # AP/AR mirrors — most tenants use stkcode === apcode === arcode.
        # Inheriting the seed's pattern would be ideal but for v1 we
        # mirror.
        self._fill_field(page, "txtstkapcode", product_code)
        self._fill_field(page, "txtstkapname", item_name)
        self._fill_field(page, "txtstkarcode", product_code)
        self._fill_field(page, "txtstkarname", item_name)

    def _fill_field(self, page, field_id: str, value: str) -> None:
        loc = page.locator(f'input[id="{field_id}"]')
        if loc.count() == 0:
            return
        loc.first.fill(value)

    def _generate_product_code(self) -> str:
        """`P{YYMM}{SEQ4}` namespace — same shape as customer codes
        but uses the stkmas listing for collision avoidance."""
        today = date.today()
        prefix = f"{DEFAULT_PRODUCT_CODE_PREFIX}{today.year % 100:02d}{today.month:02d}"
        listing = self._fetch_listing()
        existing_seqs: List[int] = []
        for row in listing:
            if row.code.startswith(prefix):
                tail = row.code[len(prefix) :]
                if tail.isdigit():
                    existing_seqs.append(int(tail))
        next_seq = (max(existing_seqs) + 1) if existing_seqs else 1
        candidate = f"{prefix}{next_seq:04d}"
        while any(r.code == candidate for r in listing):
            next_seq += 1
            candidate = f"{prefix}{next_seq:04d}"
        return candidate

    def _upsert_mapping(
        self,
        mappings: Dict[str, Any],
        item: ItemInfo,
        product_code: str,
    ) -> None:
        products = (mappings or {}).get("products") or []
        name_norm = normalize_item_name(item.name)
        for m in products:
            if (
                m.get("erp_type") == "mrerp"
                and (m.get("item_name_norm") or normalize_item_name(m.get("item_name", "")))
                == name_norm
            ):
                m["erp_code"] = product_code
                return
        products.append(
            {
                "erp_type": "mrerp",
                "item_name": item.name,
                "item_name_norm": name_norm,
                "erp_code": product_code,
            }
        )
        if isinstance(mappings, dict):
            mappings["products"] = products

    # ----- listing fetch ---------------------------------------

    def _fetch_listing(self, max_pages: int = 1) -> List[ListingProduct]:
        """A3 (Zihao 2026-05-19 拍板) · mirror of customer listing
        reliability layer: wait_for_selector + reload retry + screenshot.

        max_pages(2026-05-26 修):默认只取首页(~30 条)· 推送热路径(lookup /
        _alloc_next_code / 复核兜底 / 建后复查)只能用轻量版。大目录(实测 2060 商品)
        每笔建档失效后重取整本(69 页)= 推送卡几分钟+超时连环。只有 picker 下拉
        (list_mrerp_products)传大 max_pages 拉全量(一次性·不阻塞推送)。匹配走 _search_listing。
        """
        import time as _time

        use_cache = max_pages <= 1
        if use_cache:
            cached = self.cache.get(self._listing_cache_key)
            if cached is not None:
                return cached
        self.adapter.select_company()
        url = self.adapter.login_url + self.LISTING_PATH
        page = self.adapter._page
        last_err: Optional[Exception] = None
        for attempt in (1, 2, 3):
            try:
                if attempt == 1:
                    page.goto(
                        url,
                        wait_until="networkidle",
                        timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
                    )
                else:
                    # 退让 server 压力 + 给 PHP session 时间稳定.
                    _time.sleep(5)
                    page.reload(
                        wait_until="networkidle",
                        timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
                    )
                page.wait_for_selector(
                    "#showdata p",
                    state="attached",
                    timeout=30_000,
                )
                # 全量分页(2026-05-26):同客户列表 · #showdata 滚动驱动只 30 条 →
                # 直接 POST showdata.php 逐页拉全量(_listing_paginate)。
                rows = fetch_all_listing_pages(
                    page.request.post,
                    self.adapter.login_url,
                    self.LISTING_PATH,
                    parse_stkmas_listing,
                    max_pages=max_pages,
                )
                if use_cache:
                    self.cache.set(self._listing_cache_key, rows)
                logger.info(
                    "fetched stkmas listing: %d rows (attempt %d · max_pages=%d)",
                    len(rows),
                    attempt,
                )
                return rows
            except PWTimeout as e:
                last_err = e
                logger.warning(
                    "product listing fetch attempt %d/3 timed out: %s",
                    attempt,
                    e,
                )
                continue
            except Exception as e:
                raise MRERPTechnicalError(
                    f"product listing fetch raised: {type(e).__name__}: {e}"
                ) from e
        shot = self.adapter.save_listing_fail_screenshot("products")
        raise MRERPTechnicalError(
            f"product listing fetch failed after 3 wait+reload attempts; "
            f"screenshot={shot}; last_error={last_err}"
        )

    def _search_listing(self, query: str) -> List[ListingProduct]:
        """用 stkmas/allview.php 的 #txtsearch 按【码/名】搜**全量**商品主数据。

        镜像 mrerp_customer_sync._search_listing(2026-05-26 · P1 fail-safe 复核
        需要按码反查任意商品 · _fetch_listing 只读首页有分页上限)。

        稳健性:若搜索 UI(#txtsearch)不存在 / 选择器变了 → 回退到 _fetch_listing()
        首页扫描(已在生产验证过)· 不让 fail-safe 因 selector 漂移把整批推送炸掉。
        query 为空 → []。技术异常抛 MRERPTechnicalError 由上层(verify)兜成
        ERR_PRODUCT_VERIFY_UNAVAILABLE。
        """
        q = (query or "").strip()
        if not q:
            return []
        self.adapter.select_company()
        page = self.adapter._page
        url = self.adapter.login_url + self.LISTING_PATH
        try:
            # 2026-05-26 修:按**本模块**(stkmas)列表路径判断是否已在页上 ·
            # 旧检查 "allview.php" not in url 模块无关 → 客户复核后页停在
            # armas/allview.php,商品复核误判"已在列表页"不导航 → 在客户页搜商品码
            # → 搜不到/回退重型全量 → 假 ERR_PRODUCT_VERIFY_UNAVAILABLE。按 LISTING_PATH 精确判断。
            if self.LISTING_PATH.lower() not in (page.url or "").lower():
                page.goto(url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            # 搜索框不在 → 回退首页扫描(graceful degrade · 不硬炸)。
            if page.locator("#txtsearch").count() == 0:
                logger.info("stkmas #txtsearch not present · falling back to _fetch_listing scan")
                return self._fetch_listing()
            page.wait_for_selector("#txtsearch", state="visible", timeout=10_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"product search nav timeout: {e}") from e

        try:
            box = page.locator("#txtsearch")
            box.click()
            box.fill("")
            box.press_sequentially(q[:80], delay=30)
            try:
                page.locator("#btnsearch").click(timeout=3_000)
            except Exception:
                box.press("Enter")
            try:
                page.wait_for_load_state("networkidle", timeout=15_000)
            except PWTimeout:
                pass
            page.wait_for_timeout(1_200)
            html = page.content() or ""
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"product search failed: {e}") from e
        return parse_stkmas_listing(html)


__all__ = [
    "ItemInfo",
    "ListingProduct",
    "ProductSyncResult",
    "MRERPProductSyncService",
    "parse_stkmas_listing",
    "PRODUCT_LEVENSHTEIN_THRESHOLD_DEFAULT",
]
