# -*- coding: utf-8 -*-

"""MR.ERP 客户同步 · 查找/校验/删除/缓存 mixin(REFACTOR-WA · verbatim 0 逻辑改)"""

from __future__ import annotations

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

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

from services.erp.mrerp_customer_base import (
    BuyerInfo,
    CustomerSyncResult,
    _norm_tax,
)

logger = logging.getLogger(__name__)


class _CustomerLookupMixin:
    """lookup / lookup_or_create / verify_resolved_code / _fetch_customer_detail / invalidate / delete_customer / _upsert_mapping。"""

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
            logger.debug("customer cache hit: %s -> %s", name_norm, cached_code)
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

        # L2/L3 · 用搜索框查全量主数据(替代只读首页 ~30 条的 _fetch_listing ·
        # 2026-05-25 修:客户 > 30 个时第 31+ 个匹配不上 → 假 ERR_NO_CUSTOMER_MAPPING)。
        # fail-soft:搜不到/技术异常不阻断 · 让 lookup_or_create 走 L4 auto-create。
        try:
            listing = self._search_listing(buyer.name)
            if not listing:
                # 全名搜不到 → 用最长 token 再搜一次提召回(下方 exact/fuzzy 仍会收敛)
                token = max(
                    (w for w in re.split(r"\s+", buyer.name) if w),
                    key=len,
                    default="",
                )
                if token and token != buyer.name.strip():
                    listing = self._search_listing(token)
        except MRERPTechnicalError as e:
            logger.warning(
                "customer search failed in lookup · skipping L2/L3 · "
                "fall through to None (caller goes L4 auto-create): %s",
                e,
            )
            return None

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

        # 2026-05-25 · 自动建买方"开箱即用":没配 seed 就自动挑一个现有客户当克隆模板。
        # auto-create 走 copy-from-seed(MR.ERP 建客户表单需继承主数据引用),种子只
        # 提供 salesman/area/branch/GL 等引用,不影响业务字段 → 不再要求用户预配。
        if not seed_customer_code:
            seed_customer_code = self._resolve_default_seed()

        if not seed_customer_code:
            # 仅当主数据为空(无任何现有客户可当模板)才真失败 → 进异常。
            raise MRERPBusinessError(
                f"Auto-create needs a seed customer to clone but the MR.ERP "
                f"customer master is empty (ERR_NO_SEED_CUSTOMER). buyer={buyer.name!r}",
                failed_rows=[{"buyer_name": buyer.name, "reason_code": "ERR_NO_SEED_CUSTOMER"}],
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

    def _upsert_mapping(
        self,
        mappings: Dict[str, Any],
        client_id: int,
        customer_code: str,
    ) -> None:
        clients = (mappings or {}).get("clients") or []
        for m in clients:
            if m.get("erp_type") == "mrerp" and int(m.get("client_id") or 0) == int(client_id):
                m["erp_code"] = customer_code
                return
        clients.append(
            {
                "erp_type": "mrerp",
                "client_id": int(client_id),
                "erp_code": customer_code,
            }
        )
        if isinstance(mappings, dict):
            mappings["clients"] = clients
