# -*- coding: utf-8 -*-
"""MR.ERP 客户同步 · listing/detail 抓取 + verify + delete mixin.

从 mrerp_customer_sync.py 抽出 · 方法体一字未改(verbatim)· self.* 经 MRO 解析回主类。
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

from services.erp._matching import (
    levenshtein_ratio,
    normalize_company_name,
)
from services.erp.exceptions import (
    MRERPBusinessError,
    MRERPTechnicalError,
)
from services.erp._listing_paginate import fetch_all_listing_pages
from services.erp._customer_sync_models import (
    ListingCustomer,
)
from services.erp._customer_sync_parse import parse_armas_listing, _norm_tax

logger = logging.getLogger(__name__)


class CustomerFetchMixin:
    def verify_resolved_code(
        self,
        customer_code: str,
        buyer_name: str,
        buyer_tax_id: Optional[str] = None,
    ) -> str:
        """Fail-safe(Zihao 2026-05-26 拍板 · P1 + P2 税号优先):复核一个
        **已解析出**的 customer_code 在 MR.ERP 里对应的客户是否真的就是发票买方。

        背景:推送时 customer_code 可能来自 stale db_mapping / by-name cache /
        自动建码撞码 —— 凭 code 复用、不复核 → 静默推到错客户(实测:个人买方
        被推到 บริษัท อิ๊กลู สตูดิโอ)。本方法把"静默错推"变"响亮失败让用户修"。

        复核优先级(P2 · Zihao section 四「税号优先」):
            1. 有买方税号 → 读 ERP 客户详情页税号:
                 - 税号一致 → 放行(税号是权威标识 · 即便名字略有出入也算同一户)
                 - 税号都有但**不一致** → ERR_CUSTOMER_NAME_MISMATCH(同名不同税号 =
                   不同主体 · 必拦)
                 - 读不到 ERP 税号(详情页取不到/该客户没填税号)→ **降级到名称复核**
                   (不硬拦 · 防详情页 selector 假设出错时误杀所有推送)
            2. 名称归一化相似度 ≥ 阈值 → 放行;否则 ERR_CUSTOMER_NAME_MISMATCH。

        Returns:
            匹配时返回 MR.ERP 里的真实客户名(供日志/调试)。

        Raises:
            MRERPBusinessError(ERR_CUSTOMER_NAME_MISMATCH)  名称/税号不一致 · 不 retry。
            MRERPTechnicalError(ERR_CUSTOMER_VERIFY_UNAVAILABLE)  无法向 ERP 确认
                (listing search 技术异常/超时,或搜不到该码)· 可 retry · 不当成功。
        """
        code = (customer_code or "").strip()
        name = (buyer_name or "").strip()
        if not code or not name:
            raise MRERPTechnicalError(
                f"ERR_CUSTOMER_VERIFY_UNAVAILABLE — cannot verify "
                f"(code={code!r}, buyer={name!r} · one is empty)"
            )

        # 2026-05-26 修:复核搜索加 1 次重试 · 大目录/服务端抖动下单次易超时 →
        # 误判 ERR_CUSTOMER_VERIFY_UNAVAILABLE 把能推的发票挡下(生产实测)。
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
                f"ERR_CUSTOMER_VERIFY_UNAVAILABLE — MR.ERP listing lookup "
                f"failed for customer_code {code!r} after retry: {last_err}"
            ) from last_err

        row = next((r for r in listing if r.code == code), None)
        if row is None:
            # 搜索成功但没这个码 → 无法确认匹配 → 阻断(可 retry · 列表可能短暂抖动)。
            raise MRERPTechnicalError(
                f"ERR_CUSTOMER_VERIFY_UNAVAILABLE — customer_code {code!r} "
                f"not found in MR.ERP listing (cannot confirm it matches "
                f"buyer {name!r})"
            )

        # P2 · 税号优先:有买方税号才付出读详情页的代价(否则纯名称复核 · 不加导航)。
        buyer_tax = _norm_tax(buyer_tax_id)
        if buyer_tax:
            erp_tax = ""
            try:
                detail = self._fetch_customer_detail(code)
                erp_tax = _norm_tax((detail or {}).get("tax_id"))
            except Exception as e:  # best-effort · 失败降级名称复核 · 绝不因读详情失败硬拦
                logger.warning("customer detail tax read failed for %s: %s", code, e)
                erp_tax = ""
            if erp_tax:
                if erp_tax == buyer_tax:
                    return row.name  # 税号一致 = 权威匹配 · 放行
                raise MRERPBusinessError(
                    f"ERR_CUSTOMER_NAME_MISMATCH — resolved customer_code {code!r} "
                    f"(MR.ERP customer {row.name!r}) tax_id {erp_tax!r} does NOT match "
                    f"invoice buyer {name!r} tax_id {buyer_tax!r}",
                    failed_rows=[
                        {
                            "reason_code": "ERR_CUSTOMER_NAME_MISMATCH",
                            "customer_code": code,
                            "erp_customer_name": row.name,
                            "erp_tax_id": erp_tax,
                            "buyer_name": name,
                            "buyer_tax_id": buyer_tax,
                            "conflict": "tax_id",
                        }
                    ],
                )
            # erp_tax 读不到 → 落到下方名称复核(降级 · 不硬拦)。

        buyer_norm = normalize_company_name(name)
        erp_norm = row.name_norm or normalize_company_name(row.name)
        ratio = levenshtein_ratio(buyer_norm, erp_norm) if (buyer_norm and erp_norm) else 0.0
        if ratio >= self.customer_threshold:
            return row.name

        raise MRERPBusinessError(
            f"ERR_CUSTOMER_NAME_MISMATCH — resolved customer_code {code!r} "
            f"maps to MR.ERP customer {row.name!r} but the invoice buyer is "
            f"{name!r} (name ratio={ratio:.2f} < {self.customer_threshold})",
            failed_rows=[
                {
                    "reason_code": "ERR_CUSTOMER_NAME_MISMATCH",
                    "customer_code": code,
                    "erp_customer_name": row.name,
                    "buyer_name": name,
                    "name_ratio": round(ratio, 3),
                }
            ],
        )

    def _fetch_customer_detail(self, customer_code: str) -> Optional[Dict[str, str]]:
        """读 MR.ERP 客户详情页(armas/allform.php?id=<code>&status=view)的
        name + tax_id(P2 税号复核用)。best-effort:取不到返 None / 缺字段留空。

        view 模式表单字段 id 沿用 create 表单(txtname / txttaxid · readonly)。
        调用方必须在 adapter 的 with 块内。
        """
        code = (customer_code or "").strip()
        if not code:
            return None
        page = self.adapter._page
        url = f"{self.adapter.login_url}{self.FORM_PATH}?id={code}&status=view"
        try:
            page.goto(url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            page.wait_for_selector("input#txtname", state="attached", timeout=10_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"customer detail nav failed for {code!r}: {e}") from e
        try:
            name = page.locator("input#txtname").first.input_value()
        except Exception:
            name = ""
        try:
            tax = page.locator("input#txttaxid").first.input_value()
        except Exception:
            tax = ""
        return {"name": (name or "").strip(), "tax_id": (tax or "").strip()}

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
        del_url = f"{self.adapter.login_url}/armas/alldel.php?id={customer_code}"
        try:
            page.goto(del_url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
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
