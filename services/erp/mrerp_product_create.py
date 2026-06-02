# -*- coding: utf-8 -*-
"""MR.ERP 商品同步 · ProductCreateMixin(从 MRERPProductSyncService 巨类抽出 · 0 逻辑改)。"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

from services.erp._matching import (
    normalize_item_name,
)
from services.erp.exceptions import (
    MRERPBusinessError,
    MRERPTechnicalError,
)


from services.erp.mrerp_product_base import (
    PRODUCT_NAME_MAX,
    DEFAULT_PRODUCT_CODE_PREFIX,
    ItemInfo,
    ProductSyncResult,
    logger,
)


class ProductCreateMixin:
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
        # 2026-05-26 修:按**新码精确搜**确认是否落库 · 不能用 _fetch_listing(默认只首页 30 条)·
        # 大目录下新建的高位码不在首页 → 误判"did not appear" → 建档当失败 → 后续 NAME_MISMATCH。
        listing = self._search_listing(product_code)
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
        # 2026-05-26 修:按月份码前缀**过滤分页拉全**(只该月那批·量小)· 找真实 max+1 防撞码。
        # 此前用 _fetch_listing()(默认首页 30 条)→ 大目录看不到本月已建码 → 全给同一个码
        # (实测 5 个商品全 P26050093)→ MR.ERP 撞码 → 后续 NAME_MISMATCH。
        listing = self._fetch_listing(max_pages=400, searchdataval=prefix)
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
