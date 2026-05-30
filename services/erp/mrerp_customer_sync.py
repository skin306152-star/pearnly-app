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

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

from services.erp._master_data_cache import TTLCache
from services.erp._matching import (
    levenshtein_ratio,
)
from services.erp.exceptions import (
    MRERPTechnicalError,
)
from services.erp._listing_paginate import fetch_all_listing_pages

from services.erp.mrerp_customer_base import (  # noqa: F401
    BuyerInfo,
    ListingCustomer,
    CustomerSyncResult,
    parse_armas_listing,
    CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT,
    DEFAULT_CUSTOMER_CODE_PREFIX,
    DEFAULT_CUSTOMER_TYPE_CODE,
    DEFAULT_CUSTOMER_TYPE_LABEL,
    DEFAULT_BRANCH_CODE,
    DEFAULT_BRANCH_LABEL,
    DEFAULT_COUNTRY,
    DEFAULT_NUMERIC_TEXT,
    DEFAULT_PLACEHOLDER,
    TENANT_VALID_ACCOUNT_CODE,
    DEFAULT_CREDIT_TERM,
    DEFAULT_EXCHANGE_RATE,
    DEFAULT_CUSTOMER_RANK,
    CUSTOMER_NAME_MAX,
)
from services.erp.mrerp_customer_lookup import _CustomerLookupMixin
from services.erp.mrerp_customer_create import _CustomerCreateMixin

logger = logging.getLogger(__name__)


class MRERPCustomerSyncService(_CustomerLookupMixin, _CustomerCreateMixin):
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

    # ----- public API ------------------------------------------

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

    def _resolve_default_seed(self) -> Optional[str]:
        """没配 seed_customer_code 时,自动挑一个现有客户当 copy-from-seed 的克隆模板。

        种子仅用于继承 MR.ERP 建客户表单要求的主数据引用(salesman/area/branch/GL 等),
        新买方的业务字段(名/税号/地址)都会被覆盖 → 任一活动客户都可当模板。
        优先挑应收(ลูกหนี้การค้า)类型避免拿到非客户类型;取首页一个即可。结果缓存。
        2026-05-25 · 让"全自动建买方"开箱即用 · 不再要求用户预配种子。
        """
        if self._default_seed_cache:
            return self._default_seed_cache
        try:
            listing = self._fetch_listing()
        except MRERPTechnicalError as e:
            logger.warning("default seed resolve: listing fetch failed: %s", e)
            return None
        preferred = [r for r in listing if r.code and "ลูกหนี้" in (r.type_name or "")]
        pool = preferred or [r for r in listing if r.code and r.code.strip()]
        if not pool:
            return None
        self._default_seed_cache = pool[0].code
        logger.info("auto-picked default seed customer=%s for auto-create", pool[0].code)
        return self._default_seed_cache

    def _fetch_listing(self, max_pages: int = 1, searchdataval: str = "") -> List[ListingCustomer]:
        """Returns the parsed customer listing, hitting the in-service
        TTLCache to avoid refetching during a single push job.

        searchdataval(2026-05-26):传给 showdata.php 的过滤值 · 传月份码前缀只翻该前缀
        少量行(自动建码找真 max 完整且轻量 · 不必翻整本)· 过滤版不进缓存。

        max_pages(2026-05-26 修):默认只取首页(~30 条)· **推送热路径**(lookup /
        _alloc_next_code 防撞码 / 复核兜底 / 建后复查)只能用这个轻量版,否则大目录
        (实测 2060 商品/账套)每笔翻 69 页 × 多次建档失效重取 = 推送卡几分钟、超时连环。
        只有用户主动点的 picker 下拉(list_mrerp_*)才传大 max_pages 拉全量(可缓存·不阻塞推送)。
        匹配早已改走 _search_listing(按码/名搜·完整),不依赖本方法翻全表。

        可靠性(A3 · Zihao 2026-05-19):goto 后 wait_for_selector('#showdata p')
        catches 慢渲染 race;超时则 reload 重试;3 次仍空 → 截图 + 抛 MRERPTechnicalError。
        """
        # 缓存仅服务首页版(热路径反复取)· 全量版(picker)一次性 · 不读写缓存
        # 避免互相污染(全量写进去会让后续热路径误用 · 首页写进去会让 picker 漏数据)。
        use_cache = max_pages <= 1 and not searchdataval
        if use_cache:
            cached = self.cache.get(self._listing_cache_key)
            if cached is not None:
                return cached

        # Ensure the adapter is logged in + on the right company.
        self.adapter.select_company()
        url = self.adapter.login_url + self.LISTING_PATH
        page = self.adapter._page
        last_err: Optional[Exception] = None
        # 问题 2 加固 (Zihao 2026-05-19 拍板 · v118.34.24):
        # attempts 2 → 3 · wait_for_selector 10s → 30s · 间隔 5s 退让 server.
        import time as _time

        for attempt in (1, 2, 3):
            try:
                if attempt == 1:
                    page.goto(
                        url,
                        wait_until="networkidle",
                        timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
                    )
                else:
                    # Retry: 5s 退让 + page.reload() · 给 server 时间稳定 +
                    # 抖落 half-rendered state.
                    _time.sleep(5)
                    page.reload(
                        wait_until="networkidle",
                        timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
                    )
                # Wait specifically for the listing rows to attach (30s).
                page.wait_for_selector(
                    "#showdata p",
                    state="attached",
                    timeout=30_000,
                )
                # 全量分页(2026-05-26):#showdata 由 showdata.js 滚动驱动 ·
                # 首屏只 30 条 → 客户 > 30 个时第 31+ 个在 picker/匹配兜底里漏掉。
                # 用已登录会话直接 POST showdata.php 逐页拉全量(详见
                # _listing_paginate.fetch_all_listing_pages)。
                rows = fetch_all_listing_pages(
                    page.request.post,
                    self.adapter.login_url,
                    self.LISTING_PATH,
                    parse_armas_listing,
                    max_pages=max_pages,
                    searchdataval=searchdataval,
                )
                if use_cache:
                    self.cache.set(self._listing_cache_key, rows)
                logger.info(
                    "fetched armas listing: %d rows (attempt %d · max_pages=%d)",
                    len(rows),
                    attempt,
                    max_pages,
                )
                return rows
            except PWTimeout as e:
                last_err = e
                logger.warning(
                    "customer listing fetch attempt %d/3 timed out: %s",
                    attempt,
                    e,
                )
                continue
            except Exception as e:
                # Non-timeout: bubble up immediately so the route can
                # report a precise error code instead of a generic retry
                # cascade.
                raise MRERPTechnicalError(
                    f"customer listing fetch raised: {type(e).__name__}: {e}"
                ) from e
        # All 3 attempts timed out → screenshot + raise.
        shot = self.adapter.save_listing_fail_screenshot("customers")
        raise MRERPTechnicalError(
            f"customer listing fetch failed after 3 wait+reload attempts; "
            f"screenshot={shot}; last_error={last_err}"
        )

    def _search_listing(self, query: str) -> List[ListingCustomer]:
        """用 allview.php 的 #txtsearch 按【码/类型/名】搜**全量**客户主数据。

        2026-05-25 · 修 _fetch_listing 只读首页 ~30 条的上限:客户 > 30 个时
        第 31+ 个永远匹配不上 → 假 ERR_NO_CUSTOMER_MAPPING(实测坐实)。
        搜索框 onkeyup=searchdata(1) / #btnsearch=searchdata(2) 走 AJAX 即时重绘
        #showdata;按名搜返回候选很少(远 < 30)· 不受分页上限影响。

        注:MR.ERP 搜索只覆盖 码/类型/名 · 不含税号(税号匹配在 Pearnly 侧做)。
        query 为空 → []。搜不到 → []。技术异常抛 MRERPTechnicalError 由上层兜。
        """
        q = (query or "").strip()
        if not q:
            return []
        self.adapter.select_company()
        page = self.adapter._page
        url = self.adapter.login_url + self.LISTING_PATH
        try:
            # 2026-05-26 修:必须按**本模块**列表路径判断是否已在页上 ·
            # 旧检查 "allview.php" not in url 是模块无关的 → 客户复核后页停在
            # armas/allview.php,商品复核时误判"已在列表页"跳过导航 → 在客户页
            # 搜商品码 → 搜不到 → 假 ERR_*_VERIFY_UNAVAILABLE(同一批客户+商品复核时
            # 第二个必炸·绿色推送永远拿不到)。改为按 LISTING_PATH 精确判断。
            if self.LISTING_PATH.lower() not in (page.url or "").lower():
                page.goto(url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            page.wait_for_selector("#txtsearch", state="visible", timeout=10_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"customer search nav timeout: {e}") from e

        try:
            box = page.locator("#txtsearch")
            box.click()
            box.fill("")
            # press_sequentially 发真键事件 → 触发 onkeyup=searchdata(1)
            box.press_sequentially(q[:80], delay=30)
            # #btnsearch=searchdata(2) 更稳;回退 Enter
            try:
                page.locator("#btnsearch").click(timeout=3_000)
            except Exception:
                box.press("Enter")
            try:
                page.wait_for_load_state("networkidle", timeout=15_000)
            except PWTimeout:
                pass
            page.wait_for_timeout(1_200)  # 给 showdata.php AJAX 重绘留余量
            html = page.content() or ""
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"customer search failed: {e}") from e
        return parse_armas_listing(html)


__all__ = [
    "BuyerInfo",
    "CustomerSyncResult",
    "ListingCustomer",
    "MRERPCustomerSyncService",
    "parse_armas_listing",
    "CUSTOMER_LEVENSHTEIN_THRESHOLD_DEFAULT",
]
