# -*- coding: utf-8 -*-
"""
mrerp_adapter_masterdata.py · MRERPAdapter 主数据同步 / 校验 Mixin

从 mrerp_adapter.py 抽出（REFACTOR-WB-modularize M3 · verbatim 搬家 0 逻辑改）。
方法体一字未改;`self.X` 经 MRO 解析回主类 MRERPAdapter（构造态 + class 常量 + 其它 mixin
方法）。主类 `class MRERPAdapter(MRERPLoginMixin, MRERPUploadMixin, MRERPMasterDataMixin)` 多继承组合。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypeVar

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.exceptions import (  # noqa: E402
    MRERPBusinessError,
    MRERPTechnicalError,
)
from services.erp.mrerp_business_friendly import translate_reasons  # noqa: E402
from services.erp.mrerp_adapter_models import (  # noqa: E402
    FailedRow,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MRERPMasterDataMixin:
    # ----- master-data sync wiring (P1-B Phase 5) --------------------

    def _sync_master_data(
        self,
        histories: List[Dict[str, Any]],
        mappings: Dict[str, Any],
    ) -> None:
        """Best-effort enrichment of `mappings['clients']` from each
        history's OCR buyer fields.

        Each history can carry buyer info either at the top level
        (`buyer_name`, `buyer_tax`, `buyer_addr`) or nested under
        `history['fields']`. Anything we successfully resolve gets
        upserted into `mappings['clients']` so the downstream
        validate_history_for_sales_credit call no longer trips
        ERR_NO_CUSTOMER_MAPPING.

        Failures are SILENT here — the worst case is that validate
        catches the missing mapping a few lines later and the row
        becomes a FailedRow with `ERR_NO_CUSTOMER_MAPPING`. That's
        cleaner than raising mid-batch and losing the other histories.

        If `master_data_auto_create=True` is set, lookup_or_create runs
        and may itself raise MRERPBusinessError (currently happens on
        TEST2019 due to the master-data validation blocker — see
        mrerp_customer_sync._layer4_auto_create docstring). We capture
        the exception and continue; validate will then catch the row
        as a missing mapping.
        """
        if not self.enable_master_data_sync:
            return
        if self._customer_sync is None:
            from services.erp.mrerp_customer_sync import (
                MRERPCustomerSyncService,
            )

            self._customer_sync = MRERPCustomerSyncService(self)
        for h in histories:
            buyer = self._extract_buyer(h)
            if buyer is None:
                continue
            # 问题 A (Zihao 2026-05-19 拍板 · v118.34.25) · history.client_id
            # 是 0/null 时跳过 customer sync. 没 client_id 走到 L2 listing
            # 抓取浪费 90s+(30s × 3 retries) · 而且 preflight 接着会 ERR_NO_CLIENT
            # · 早返让用户看到清晰的错而不是 "listing fetch failed".
            if not (buyer.client_id and buyer.client_id > 0):
                logger.info(
                    "master-data sync skipped (no client_id assigned) for buyer=%r",
                    buyer.name,
                )
                continue
            try:
                if self.master_data_auto_create:
                    result = self._customer_sync.lookup_or_create(
                        buyer,
                        mappings,
                        seed_customer_code=self.seed_customer_code,
                    )
                else:
                    result = self._customer_sync.lookup(buyer, mappings)
                if result is None:
                    continue
                # Persist into mappings so validate_history finds it.
                if buyer.client_id:
                    self._customer_sync._upsert_mapping(
                        mappings,
                        buyer.client_id,
                        result.customer_code,
                    )
            except MRERPBusinessError as e:
                # Auto-create raised — let validate catch the missing
                # mapping downstream so the FailedRow message names the
                # specific invoice.
                logger.info(
                    "master-data sync skipped for buyer=%r: %s",
                    buyer.name,
                    e,
                )
            except MRERPTechnicalError as e:
                # 问题 a (Zihao 2026-05-19 拍板 · v118.34.26) · listing fetch
                # timeout 等 technical · 不让 sync 把整批 push 炸掉. swallow +
                # log warning · 让 validate_history_for_sales_credit 后面
                # ERR_NO_CUSTOMER_MAPPING preflight 早返友好错给用户.
                logger.warning(
                    "master-data sync technical fail (continuing) for buyer=%r: %s",
                    buyer.name,
                    e,
                )

        # Phase 5 extension: per-item product enrichment. Same
        # opt-in / opt-out shape as the buyer branch above.
        if self._product_sync is None:
            from services.erp.mrerp_product_sync import (
                MRERPProductSyncService,
            )

            self._product_sync = MRERPProductSyncService(self)
        for h in histories:
            # 问题 A 镜像 (v118.34.25) · 没 client_id 也跳过 product sync ·
            # 没归属到客户的发票 · 推都推不出去 · 没必要预先拉 stkmas listing.
            if not (h.get("client_id") and int(h.get("client_id") or 0) > 0):
                continue
            items = self._extract_items(h)
            for item in items:
                try:
                    # P1「开箱即用」· 通用模式(配了 generic_product_code)下商品
                    # 只 lookup 命中真实商品(精准),对不上不建档 —— 兜底通用码在
                    # generator/verify 处理。仅精确模式(未配通用码)才逐行 auto-create。
                    if self.master_data_auto_create and not self.generic_product_code:
                        result = self._product_sync.lookup_or_create(
                            item,
                            mappings,
                            seed_product_code=self.seed_product_code,
                        )
                    else:
                        result = self._product_sync.lookup(item, mappings)
                    if result is None:
                        continue
                    self._product_sync._upsert_mapping(
                        mappings,
                        item,
                        result.product_code,
                    )
                except MRERPBusinessError as e:
                    logger.info(
                        "product master-data sync skipped for item=%r: %s",
                        item.name,
                        e,
                    )
                except MRERPTechnicalError as e:
                    # 问题 a 镜像 (v118.34.26) · listing fetch timeout 不炸整批 ·
                    # validate 接下来 ERR_NO_CUSTOMER_MAPPING 早返友好错.
                    logger.warning(
                        "product master-data sync technical fail (continuing) for item=%r: %s",
                        item.name,
                        e,
                    )

    def _verify_resolved_master_data(
        self,
        histories: List[Dict[str, Any]],
        mappings: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[FailedRow]]:
        """Fail-safe 复核 gate(Zihao 2026-05-26 拍板 · P1)。

        在 generate_xlsx 之前 · 对每张 history **解析出最终要推送的**
        customer_code(同 generator 的 lookup_customer_code)和各商品行的
        product_code(同 generator 的 _resolve_product_code · 含 fallback '123'),
        用 MR.ERP listing 反查真名复核是否匹配买方/商品:

          - 不匹配 → 该 history 不推 · 变 FailedRow(ERR_*_NAME_MISMATCH · 用户改映射)
          - 无法确认(search 超时/搜不到)→ 不推 · FailedRow(ERR_*_VERIFY_UNAVAILABLE
            · 技术错可 retry · 但绝不显示成功)

        为什么在这里而不在 Sync 服务内部:推送时 customer/product code 直接从
        `mappings`(已含 DB 里的 stale 映射 + generator 的 '123' fallback)取 ·
        绕过了 Sync.lookup 的解析路径 · 所以复核必须卡在"最终码"这一关。

        Returns (still_valid_histories, failed_rows)。复核需要 live MR.ERP listing,
        故懒创建 Sync 服务(不依赖 enable_master_data_sync 开关 · 安全复核对所有
        MR.ERP 推送都生效)。
        """
        from services.erp import mrerp_xlsx_generator as _gen

        if self._customer_sync is None:
            from services.erp.mrerp_customer_sync import MRERPCustomerSyncService

            self._customer_sync = MRERPCustomerSyncService(self)
        if self._product_sync is None:
            from services.erp.mrerp_product_sync import MRERPProductSyncService

            self._product_sync = MRERPProductSyncService(self)

        from services.erp._matching import normalize_company_name, normalize_item_name

        product_lookup = _gen._build_product_lookup(mappings)

        # P1「开箱即用」· 通用商品码(配了才有)· 不中的行挂它,只验它"存在"一次。
        generic_code = (mappings.get("_generic_product_code") or "").strip() or None

        # 复核结果 memo(防同一 (code,名) 在批内反复 search)· 值=reason_code 或 None(通过)。
        cust_memo: Dict[tuple, Optional[str]] = {}
        prod_memo: Dict[tuple, Optional[str]] = {}
        # 通用码存在性 memo · 按码(不含名)· 整批最多 search 一次。
        generic_memo: Dict[str, Optional[str]] = {}

        def _verify_customer(code: str, buyer_name: str, buyer_tax_id: str) -> Optional[str]:
            # P2 · memo key 含税号(同码不同税号要分别复核)。
            key = (code, normalize_company_name(buyer_name or ""), (buyer_tax_id or "").strip())
            if key in cust_memo:
                return cust_memo[key]
            reason: Optional[str] = None
            try:
                self._customer_sync.verify_resolved_code(code, buyer_name, buyer_tax_id)
            except MRERPBusinessError:
                reason = "ERR_CUSTOMER_NAME_MISMATCH"
            except MRERPTechnicalError:
                reason = "ERR_CUSTOMER_VERIFY_UNAVAILABLE"
            cust_memo[key] = reason
            return reason

        def _verify_product(code: str, item_name: str) -> Optional[str]:
            key = (code, normalize_item_name(item_name or ""))
            if key in prod_memo:
                return prod_memo[key]
            reason: Optional[str] = None
            try:
                self._product_sync.verify_resolved_code(code, item_name)
            except MRERPBusinessError:
                reason = "ERR_PRODUCT_NAME_MISMATCH"
            except MRERPTechnicalError:
                reason = "ERR_PRODUCT_VERIFY_UNAVAILABLE"
            prod_memo[key] = reason
            return reason

        def _verify_generic_exists(code: str) -> Optional[str]:
            # P1「开箱即用」· 通用商品码只验"在 ERP 里存在"(整批一次)· 不做名字
            # 匹配(行描述本就和通用品名不同)。这是把 130 秒(逐行反查)降到秒级的关键。
            if code in generic_memo:
                return generic_memo[code]
            reason: Optional[str] = None
            try:
                self._product_sync.verify_code_exists(code)
            except MRERPTechnicalError:
                # 通用码在 ERP 找不到(被删/配错)· 不静默 · 响亮失败让用户回连接重选。
                reason = "ERR_PRODUCT_VERIFY_UNAVAILABLE"
            generic_memo[code] = reason
            return reason

        still_valid: List[Dict[str, Any]] = []
        failed: List[FailedRow] = []
        for h in histories:
            reason: Optional[str] = None

            # 1) 客户复核 — 仅当能解析出 code + 有买方名(否则无名可比 · 维持原行为)。
            cid = int(h.get("client_id") or 0)
            customer_code = _gen.lookup_customer_code(cid, mappings)
            buyer = self._extract_buyer(h)
            buyer_name = buyer.name if buyer else ""
            buyer_tax_id = (buyer.tax_id if buyer else "") or ""
            if customer_code and buyer_name:
                reason = _verify_customer(customer_code, buyer_name, buyer_tax_id)

            # 2) 商品复核 — 客户先过才查商品(失败已定 · 省 search)。
            if reason is None:
                for item in self._extract_items(h):
                    real_code = _gen._resolve_product_code(item.name, product_lookup)
                    if real_code:
                        # 命中 ERP 已有真实商品 → 按码反查真名复核(含截断容忍)。
                        r = _verify_product(real_code, item.name)
                    elif generic_code:
                        # P1 通用模式 · 对不上 → 挂通用码,只验通用码存在(整批一次)。
                        r = _verify_generic_exists(generic_code)
                    else:
                        # 精确模式且对不上 → 老行为:fallback '123' → 名复核必失败(响亮)。
                        r = _verify_product("123", item.name)
                    if r is not None:
                        reason = r
                        break

            if reason is None:
                still_valid.append(h)
                continue

            inv_no = (
                _gen.derive_mrerp_invoice_no(h)
                if h.get("invoice_date")
                else (h.get("invoice_number") or h.get("invoice_no") or "?")
            )
            logger.warning(
                "fail-safe verify blocked push for invoice %s: %s",
                inv_no,
                reason,
            )
            failed.append(
                FailedRow(
                    invoice_no=inv_no,
                    reasons=[reason],
                    reasons_friendly=translate_reasons([reason]),
                    original=h,
                )
            )
        return still_valid, failed
