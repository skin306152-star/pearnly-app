# -*- coding: utf-8 -*-
"""MR.ERP 商品同步 · ProductListingMixin(从 MRERPProductSyncService 巨类抽出 · 0 逻辑改)。"""

from __future__ import annotations

from typing import List, Optional

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

from services.erp.exceptions import (
    MRERPTechnicalError,
)
from services.erp._listing_paginate import fetch_all_listing_pages


from services.erp.mrerp_product_base import (
    ListingProduct,
    parse_stkmas_listing,
    logger,
)


class ProductListingMixin:
    def _fetch_listing(self, max_pages: int = 1, searchdataval: str = "") -> List[ListingProduct]:
        """A3 (Zihao 2026-05-19 拍板) · mirror of customer listing
        reliability layer: wait_for_selector + reload retry + screenshot.

        searchdataval(2026-05-26):传给 showdata.php 的过滤值(月份码前缀)· 只翻少量行 ·
        自动建码找真 max 完整且轻量 · 过滤版不进缓存。

        max_pages(2026-05-26 修):默认只取首页(~30 条)· 推送热路径(lookup /
        _alloc_next_code / 复核兜底 / 建后复查)只能用轻量版。大目录(实测 2060 商品)
        每笔建档失效后重取整本(69 页)= 推送卡几分钟+超时连环。只有 picker 下拉
        (list_mrerp_products)传大 max_pages 拉全量(一次性·不阻塞推送)。匹配走 _search_listing。
        """
        import time as _time

        use_cache = max_pages <= 1 and not searchdataval
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
                    searchdataval=searchdataval,
                )
                if use_cache:
                    self.cache.set(self._listing_cache_key, rows)
                logger.info(
                    "fetched stkmas listing: %d rows (attempt %d · max_pages=%d)",
                    len(rows),
                    attempt,
                    max_pages,
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
