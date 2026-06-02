# -*- coding: utf-8 -*-
"""MR.ERP 商品同步 · ProductLookupMixin(从 MRERPProductSyncService 巨类抽出 · 0 逻辑改)。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


from services.erp._matching import (
    levenshtein_ratio,
    normalize_item_name,
)
from services.erp.exceptions import (
    MRERPBusinessError,
    MRERPTechnicalError,
)


from services.erp.mrerp_product_base import (
    ItemInfo,
    ListingProduct,
    ProductSyncResult,
    logger,
)


class ProductLookupMixin:
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
        # 2026-05-26 修:MR.ERP 商品名字段有长度上限,长描述商品(泰式烘焙长名带规格/换行,
        # 100+ 字)建档时被**截断** → ERP 存的是发票名的前缀。复核时拿"完整发票名 vs 截断名"
        # 算相似度恒 < 阈值(实测 0.30)→ 自动建出来的长名商品永远推不成。
        # 截断前缀匹配:ERP 归一名是发票归一名的前缀且足够长(≥8 字符防误命中)→ 判为同一商品。
        truncated_match = bool(erp_norm) and len(erp_norm) >= 8 and item_norm.startswith(erp_norm)
        ratio = levenshtein_ratio(item_norm, erp_norm) if (item_norm and erp_norm) else 0.0
        if truncated_match or ratio >= self.product_threshold:
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

    def verify_code_exists(self, product_code: str) -> str:
        """P1「开箱即用」· 只验一个 product_code 在 MR.ERP 里**存在**,不做名字匹配。

        用于通用商品码(generic_product_code)兜底:对不上真实商品的发票行都挂这个
        通用销售商品,行描述用 OCR 原名。通用码是用户连接时从 ERP 商品列表选的,
        本就是已有真实商品 · 不需要逐行拿"行描述 vs 通用品名"做相似度(必然不像)。
        只需确认它还在(防被删/配错 → A6 种子失效),整批 search 一次即可。

        Returns: MR.ERP 里该码的真实商品名(确认存在)。
        Raises:  MRERPTechnicalError — 搜不到该码 / listing 技术异常(无法确认存在)。
        """
        code = (product_code or "").strip()
        if not code:
            raise MRERPTechnicalError(
                "ERR_PRODUCT_VERIFY_UNAVAILABLE — generic product_code is empty "
                "(连接里没配通用销售商品码)"
            )
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
                f"ERR_PRODUCT_VERIFY_UNAVAILABLE — MR.ERP listing lookup failed "
                f"for generic product_code {code!r} after retry: {last_err}"
            ) from last_err
        row = next((r for r in listing if r.code == code), None)
        if row is None:
            raise MRERPTechnicalError(
                f"ERR_PRODUCT_VERIFY_UNAVAILABLE — generic product_code {code!r} "
                f"not found in MR.ERP listing(可能被删或配错 · 请回连接重选通用商品)"
            )
        return row.name

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
