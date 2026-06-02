# -*- coding: utf-8 -*-
"""MR.ERP 客户同步 · 解析层(L1 db / L2 exact / L3 fuzzy)+ seed + db upsert mixin.

从 mrerp_customer_sync.py 抽出 · 方法体一字未改(verbatim)· self.* 经 MRO 解析回主类。
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional


from services.erp._matching import (
    levenshtein_ratio,
    normalize_company_name,
)
from services.erp.exceptions import (
    MRERPBusinessError,
    MRERPTechnicalError,
)
from services.erp._customer_sync_models import (
    BuyerInfo,
    ListingCustomer,
    CustomerSyncResult,
)

logger = logging.getLogger(__name__)


class CustomerResolveMixin:
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
