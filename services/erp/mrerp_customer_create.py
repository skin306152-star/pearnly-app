# -*- coding: utf-8 -*-
"""MR.ERP 客户同步 · Layer4 自动建档/填表 mixin(REFACTOR-WA · verbatim 0 逻辑改)"""

from __future__ import annotations

import logging
from datetime import date
from typing import List

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

from services.erp.exceptions import (
    MRERPBusinessError,
    MRERPTechnicalError,
)

from services.erp.mrerp_customer_base import (
    BuyerInfo,
    CustomerSyncResult,
    DEFAULT_CUSTOMER_CODE_PREFIX,
    CUSTOMER_NAME_MAX,
)

logger = logging.getLogger(__name__)


class _CustomerCreateMixin:
    """_layer4_auto_create + _copy_from_seed/_override_after_copy/_fill_*/_generate_customer_code。"""

    def _layer4_auto_create(
        self,
        buyer: BuyerInfo,
        seed_customer_code: str,
    ) -> CustomerSyncResult:
        """Create a new customer row by cloning a seed customer and
        overriding the four fields that are unique to the new row.

        Flow (per [mrerp-customer-copy-flow.md](../../docs/integrations/mrerp-customer-copy-flow.md)):
          1. nav armas/allform.php (blank form)
          2. click #inpdupdata ("สำเนา") → opens bshlistbox popup
          3. wait ~3s for AJAX-populated candidate list
          4. click the seed row in #bshlistboxdetail
          5. ~all 45 fields populate from the seed (incl. all hidden
             master-data IDs and code/detail triplets)
          6. override txtarcode (generated) + txtname (buyer.name)
             + txttaxid (OCR or random) + txtaddr1..4 (OCR address)
          7. click #btnsave → checknull() passes → allsave.php
          8. verify by listing fetch

        The earlier "fill placeholders" path is gone — it was rejected
        by the server with `alert("Data is use in the system")` because
        the placeholder codes weren't real master-data rows. The copy
        flow inherits valid refs by construction.
        """
        if not seed_customer_code:
            raise MRERPBusinessError(
                "ERR_NO_SEED_CUSTOMER — seed_customer_code is required",
                failed_rows=[{"buyer_name": buyer.name, "reason_code": "ERR_NO_SEED_CUSTOMER"}],
            )

        page = self.adapter._page

        # 1) Pick a unique customer code.
        customer_code = self._generate_customer_code()

        target = self.adapter.login_url + self.FORM_PATH
        try:
            page.goto(target, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"customer-create form nav timeout: {e}") from e

        # Bug 8 fix (Zihao 2026-05-19 拍板 · v118.34.23) · session bounce 检测 ·
        # 跟 mrerp_product_sync 镜像 · armas/allform.php 也可能在长 batch 后被
        # MR.ERP 服务端无声 invalidate session.
        landed_url = page.url or ""
        if "/login/login.php" in landed_url:
            logger.warning("[customer-create] nav bounced to login.php · re-login + retry")
            try:
                self.adapter._logged_in = False
                self.adapter._company_selected = False
                self.adapter.login()
                self.adapter.select_company()
                page.goto(target, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            except Exception as e:
                raise MRERPTechnicalError(
                    f"customer-create session re-login failed: {type(e).__name__}: {e}"
                ) from e
            landed_url = page.url or ""

        # Sanity: confirm we're on the create form.
        if "allform.php" not in landed_url:
            raise MRERPTechnicalError(
                f"customer-create nav landed on {landed_url}, not allform.php "
                f"(session refresh did not recover)"
            )

        # 2-5) Copy-from-seed.
        try:
            self._copy_from_seed(page, seed_customer_code)
        except MRERPBusinessError:
            raise
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"copy-from-seed flow timeout: {e}") from e

        # 6) Override the fields that must be unique to the new row.
        try:
            self._override_after_copy(page, customer_code, buyer)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"override-after-copy timeout: {e}") from e

        # 7) Click save.
        dialogs_before = len(self.adapter._session.dialogs) if self.adapter._session else 0
        try:
            page.click('button[id="btnsave"]', timeout=5_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"customer-create save click timeout: {e}") from e

        try:
            page.wait_for_load_state("networkidle", timeout=self.SAVE_TIMEOUT_MS)
        except PWTimeout:
            pass
        page.wait_for_timeout(1_500)

        if self.adapter._session:
            new_dialogs = self.adapter._session.dialogs[dialogs_before:]
        else:
            new_dialogs = []

        # 8) Verify by search (按码搜全量 · 不再用只读 30 条的 _fetch_listing ·
        #    2026-05-25 修:新建客户排在 30 名后会被误判"did not appear")。
        self.invalidate()
        try:
            listing = self._search_listing(customer_code)
        except MRERPTechnicalError:
            listing = self._fetch_listing()  # 搜索异常兜底回退首页扫描
        if any(r.code == customer_code for r in listing):
            # P3 闭环反查(Zihao 2026-05-26 section 五):建完再复核新码对应的客户
            # 名/税号确实 == 发票买方 · 防"自动建码撞到已存在的别家客户"残留风险。
            # 名/税号冲突(BusinessError)→ 抛(建出来的不是买方 · 不推)。
            # 反查不可用(TechnicalError)→ 降级:刚写的就是买方数据 · 可信 · 仅 log。
            try:
                self.verify_resolved_code(customer_code, buyer.name, buyer.tax_id)
            except MRERPBusinessError:
                raise
            except MRERPTechnicalError as e:
                logger.warning(
                    "auto-create post-verify unavailable for %s (trusting just-written "
                    "buyer data): %s",
                    customer_code,
                    e,
                )
            logger.info(
                "auto-created customer %s (seed=%s, buyer=%s)",
                customer_code,
                seed_customer_code,
                buyer.name,
            )
            return CustomerSyncResult(
                customer_code=customer_code,
                source="erp_auto_created",
                confidence=1.0,
                matched_name=buyer.name,
                is_new=True,
                erp_code_persisted=False,
            )

        dialog_text = " / ".join(d for d in new_dialogs)[:300]
        raise MRERPBusinessError(
            f"customer auto-create did not appear in listing "
            f"(code={customer_code}, seed={seed_customer_code}, "
            f"dialogs={dialog_text!r})",
            failed_rows=[
                {
                    "buyer_name": buyer.name,
                    "customer_code_attempted": customer_code,
                    "seed_customer_code": seed_customer_code,
                    "dialogs": new_dialogs,
                }
            ],
        )

    def _copy_from_seed(self, page, seed_customer_code: str) -> None:
        """Drive the inpdupdata picker to clone `seed_customer_code`
        into the current form.

        🛠 Patch 1 (Zihao 2026-05-18 拍板): the armas popup uses the
        same virtual-scroll pattern as stkmas — at TEST2019 scale (2
        customers) all rows are in the DOM, but on accounting-firm
        tenants with 50+ customers only ~10 fit at a time. We now use
        the popup's built-in `#bshlistboxinpsearch` input to filter
        down to just the seed before clicking, mirroring the
        `mrerp_product_sync._copy_from_seed` implementation.
        """
        loc = page.locator("input#inpdupdata")
        if loc.count() == 0:
            raise MRERPTechnicalError(
                "inpdupdata (copy) button missing — MR.ERP UI may have " "changed"
            )
        loc.first.click(timeout=5_000)

        # Wait for the popup search input (faster signal than
        # detailshow's first <p>; the search input renders before AJAX
        # populates the rows).
        try:
            page.wait_for_selector(
                "#bshlistboxinpsearch",
                state="visible",
                timeout=10_000,
            )
        except PWTimeout as e:
            raise MRERPTechnicalError(f"copy picker popup did not render: {e}") from e
        page.wait_for_timeout(500)

        # Type the seed code into the popup's search input. The onkeyup
        # handler `bshdatalistbox()` re-renders the visible rows in
        # real time — only matching ones survive.
        search = page.locator("input#bshlistboxinpsearch")
        try:
            search.fill(seed_customer_code)
            # bshdatalistbox is wired to onkeyup — fire one to trigger
            # the filter, then settle.
            search.press("End")
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"copy picker search input failed: {e}") from e
        page.wait_for_timeout(800)

        # Stricter selector first (exact text-is on the code span), then
        # a fallback substring match in case the code contains
        # characters that confuse text-is().
        row = page.locator(
            "#bshlistboxdetailshow p" f":has(span:text-is({seed_customer_code!r}))"
        ).first
        if row.count() == 0:
            row = page.locator("#bshlistboxdetailshow p" f":has-text({seed_customer_code!r})").first
        if row.count() == 0:
            raise MRERPBusinessError(
                f"seed customer {seed_customer_code!r} not visible in "
                f"the copy picker — confirm the code exists in this "
                f"tenant's customer master (searched via "
                f"bshlistboxinpsearch)",
                failed_rows=[
                    {
                        "reason_code": "ERR_SEED_NOT_FOUND",
                        "seed_customer_code": seed_customer_code,
                    }
                ],
            )

        try:
            row.click(timeout=3_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"seed row click failed: {e}") from e

        # bshlistboxafterselectdata fires an AJAX fetch to populate the
        # form with the seed's full field set. ~1-2s.
        page.wait_for_timeout(2_500)

        try:
            populated_name = page.locator("input#txtname").first.input_value()
        except Exception:
            populated_name = ""
        if not populated_name:
            raise MRERPTechnicalError(
                "copy picker click did not populate the form " "(txtname still empty)"
            )

    def _override_after_copy(
        self,
        page,
        customer_code: str,
        buyer: BuyerInfo,
    ) -> None:
        """Replace the seed's identity fields with the new customer's.

        Per [mrerp-customer-copy-flow.md §5](../../docs/integrations/mrerp-customer-copy-flow.md):
        leave master-data refs alone; override only the 4 unique fields.
        """
        # Customer code is editable text — direct fill is fine.
        self._fill_field(page, "txtarcode", customer_code)
        # Customer name — truncate to MR.ERP's ceiling.
        self._fill_field(
            page,
            "txtname",
            (buyer.name or "")[:CUSTOMER_NAME_MAX],
        )

        # Tax ID — use OCR if available + 13 digits, else random.
        tax_id = (buyer.tax_id or "").strip()
        if len(tax_id) == 13 and tax_id.isdigit():
            self._fill_field(page, "txttaxid", tax_id)
        else:
            import secrets

            rand_tin = str(secrets.randbelow(10**12) + 10**12)[:13]
            self._fill_field(page, "txttaxid", rand_tin)

        # Address override — only when buyer has one (otherwise inherit
        # seed's placeholder address; harmless).
        if buyer.address:
            self._fill_addresses(page, buyer.address)

    def _fill_field(self, page, field_id: str, value: str) -> None:
        loc = page.locator(f'input[id="{field_id}"]')
        if loc.count() == 0:
            return
        loc.first.fill(value)

    def _fill_code_detail_pair(
        self,
        page,
        code_field_id: str,
        code_value: str,
        *,
        fallback_detail: str = "",
    ) -> None:
        """For inputs that live in a "code + hidden val + detail label"
        triplet (e.g. txtrectype/rectypeval/txtrectypedetail), inject the
        values directly via JS.

        Why JS, not Playwright fill():
          The visible 'code' inputs (txtrectype / txtacfile / txtemp /
          etc.) are marked `readonly` because the real UX is "click the
          input → bshlistbox opens a popup-picker → click an option →
          JS writes back". Playwright's `fill()` rejects readonly
          elements. We bypass the popup by setting the visible value,
          the hidden 'val' that the server actually consumes, and the
          'detail' label so the saved row looks right in MR.ERP's
          listing/edit pages.

        Hidden + detail id naming convention (from probe):
          txt<base>   →  visible 'code' input (readonly)
          <base>val   →  hidden id consumed server-side
          txt<base>detail  →  visible label that auto-fills on pick
        """
        if not code_field_id.startswith("txt"):
            return
        base = code_field_id[3:]
        hidden_id = f"{base}val"
        detail_id = f"{code_field_id}detail"

        import json as _json

        js = """(function(code, fallback, codeId, hiddenId, detailId) {
            var f = document.getElementById(codeId);
            if (f) {
                try { f.removeAttribute('readonly'); } catch(e) {}
                f.value = code;
                try { f.dispatchEvent(new Event('change', {bubbles: true})); } catch(e) {}
            }
            var h = document.getElementById(hiddenId);
            if (h) h.value = code;
            var d = document.getElementById(detailId);
            if (d) d.value = fallback;
            return {
                visible: f ? f.value : null,
                hidden: h ? h.value : null,
                detail: d ? d.value : null
            };
        })""" + (
            f"({_json.dumps(code_value)}, {_json.dumps(fallback_detail)}, "
            f"{_json.dumps(code_field_id)}, {_json.dumps(hidden_id)}, "
            f"{_json.dumps(detail_id)})"
        )
        try:
            result = page.evaluate(js)
            logger.debug(
                "code-detail fill %s -> %s",
                code_field_id,
                result,
            )
        except Exception as e:
            logger.warning(
                "JS fill for %s failed: %s",
                code_field_id,
                e,
            )

    def _fill_addresses(self, page, address: str) -> None:
        # MR.ERP accepts up to 4 address lines, each TBD-len. Split by
        # newline if present; otherwise just put the whole string in
        # addr1.
        parts = [p.strip() for p in (address or "").split("\n") if p.strip()]
        if not parts:
            return
        for i, p in enumerate(parts[:4], start=1):
            self._fill_field(page, f"txtaddr{i}", p[:80])

    def _generate_customer_code(self) -> str:
        """在 P{YYMM}{SEQ4} 命名空间里挑一个**全量唯一**的客户码。

        2026-05-25 修:旧实现只扫首页 ~30 条列表算 max+1 → 首页 max 恒为已有最大
        (如 028)→ 每次都生成同一个码(029)→ 多个买方撞同一客户码(实测坐实 ·
        推送会指向错误客户)。改用搜索框(查全量)逐个确认候选码不存在。
        """
        import random

        today = date.today()
        prefix = f"{DEFAULT_CUSTOMER_CODE_PREFIX}{today.year % 100:02d}{today.month:02d}"
        # 2026-05-26 修:按月份码前缀**过滤分页拉全**(只该月那批·量小)→ 真实 max+1 ·
        # 起点准了基本一次命中。此前用 _fetch_listing(首页 30 条)起点偏小 + 搜索校验偶发
        # 返空 → 误判候选码可用 → 撞到已有客户(实测 P26050038 撞旧买方 → NAME_MISMATCH)。
        try:
            listing = self._fetch_listing(max_pages=400, searchdataval=prefix)
        except MRERPTechnicalError:
            listing = []
        existing_seqs: List[int] = []
        for row in listing:
            if row.code.startswith(prefix):
                tail = row.code[len(prefix) :]
                if tail.isdigit():
                    existing_seqs.append(int(tail))
        next_seq = (max(existing_seqs) + 1) if existing_seqs else 1

        # 全量唯一性校验:用搜索框查候选码 · 精确命中即撞 → +1 重试(最多 60 次)。
        candidate = f"{prefix}{next_seq:04d}"
        for _ in range(60):
            try:
                hits = self._search_listing(candidate)
            except MRERPTechnicalError:
                return candidate  # 搜不了 → 用当前候选回退 · 不阻断建客户
            if not any(r.code == candidate for r in hits):
                return candidate  # 全量无此码 → 唯一
            next_seq += 1
            candidate = f"{prefix}{next_seq:04d}"
        # 兜底:60 连撞(极不可能)→ 随机 4 位
        return f"{prefix}{random.randint(1, 9999):04d}"
