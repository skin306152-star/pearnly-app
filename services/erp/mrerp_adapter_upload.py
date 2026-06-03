# -*- coding: utf-8 -*-
"""
mrerp_adapter_upload.py · MRERPAdapter 上传批次 / 列表分类 / 查删 Mixin

从 mrerp_adapter.py 抽出（REFACTOR-WB-modularize M2 · verbatim 搬家 0 逻辑改）。
方法体一字未改;`self.X` 经 MRO 解析回主类 MRERPAdapter（构造态 + class 常量 + 其它 mixin
方法）。主类 `class MRERPAdapter(MRERPLoginMixin, MRERPUploadMixin, MRERPMasterDataMixin)` 多继承组合。
"""

from __future__ import annotations

import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp import mrerp_xlsx_generator  # noqa: E402
from services.erp.exceptions import (  # noqa: E402
    MRERPAuthError,
    MRERPTechnicalError,
)
from services.erp.mrerp_business_friendly import translate_reasons  # noqa: E402
from services.erp.mrerp_report_parser import (  # noqa: E402
    ImportReport,
    parse_import_report,
)
from services.erp.mrerp_adapter_models import (  # noqa: E402
    FailedRow,
    ImportResult,
    InvoiceRecord,
    SuccessRow,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MRERPUploadMixin:
    # ----- upload batch ----------------------------------------------

    def upload_invoice_batch(
        self,
        histories: List[Dict[str, Any]],
        mappings: Dict[str, Any],
    ) -> ImportResult:
        """End-to-end: generate xlsx -> upload -> preview -> confirm ->
        download report -> parse.

        Authenticates and selects company if not already done. Returns an
        ImportResult that classifies every input invoice as success or
        failed, with reasons sourced from the report xlsx's หมายเหตุ column.

        Raises:
            MRERPAuthError       — session expired mid-batch; caller should
                                   re-issue credentials
            MRERPTechnicalError  — Playwright timeouts / 5xx that survived
                                   the configured retry budget
            MRERPBusinessError   — the xlsx itself was rejected before any
                                   per-row notes could be returned
                                   (e.g. preview page is empty)
        """
        if not histories:
            return ImportResult(total=0)

        # P1「开箱即用」· 把通用商品码注入共享 mappings,供 verify gate +
        # xlsx generator 读取(避免穿透多层函数签名)。None = 精确模式。
        if isinstance(mappings, dict):
            mappings["_generic_product_code"] = self.generic_product_code

        self.select_company()
        t0 = time.time()

        # P1-B Phase 5 · master-data sync preflight.
        # When enabled, runs BEFORE validate_history_for_sales_credit so
        # the validator sees the enriched mappings and stops surfacing
        # ERR_NO_CUSTOMER_MAPPING for buyers that already exist in MR.ERP
        # (or that we just auto-created). Opt-in via constructor flag to
        # avoid breaking callers that have already curated their own
        # client→erp_code mappings.
        if self.enable_master_data_sync:
            self._sync_master_data(histories, mappings)

        # P1-A §3.1-§3.5 · client-side preflight before touching the
        # browser. Rejects field-length overflow, negative amount,
        # invalid tax kind, far-future dates etc. up front so we don't
        # waste an upload round-trip (and so the user sees the real
        # root cause instead of MR.ERP's "length too long" mask).
        preflight_failed: List[FailedRow] = []
        valid_histories: List[Dict[str, Any]] = []
        for h in histories:
            ok, err_code, warnings = mrerp_xlsx_generator.validate_history_for_sales_credit(
                h,
                mappings,
            )
            if warnings:
                logger.info(
                    "preflight warnings for %s: %s",
                    h.get("invoice_number") or h.get("invoice_no") or "?",
                    warnings,
                )
            if ok:
                valid_histories.append(h)
                continue
            inv_no = (
                mrerp_xlsx_generator.derive_mrerp_invoice_no(h)
                if h.get("invoice_date")
                else (h.get("invoice_number") or h.get("invoice_no") or "?")
            )
            reasons = [err_code or "ERR_UNKNOWN_PREFLIGHT"]
            preflight_failed.append(
                FailedRow(
                    invoice_no=inv_no,
                    reasons=reasons,
                    reasons_friendly=translate_reasons(reasons),
                    original=h,
                )
            )

        if not valid_histories:
            # Every history was rejected at preflight; nothing to upload.
            result = ImportResult(total=len(histories))
            result.failed = preflight_failed
            result.elapsed_ms = int((time.time() - t0) * 1000)
            return result

        # P1 fail-safe 名字复核 gate(Zihao 2026-05-26 拍板)· 在生成 xlsx 前 ·
        # 对每张发票将要推送的 customer_code / product_code 反查 MR.ERP 真名复核 ·
        # 不匹配/无法确认的不推 · 变 FailedRow(响亮失败)· 杜绝静默错推到错客户/占位商品。
        valid_histories, verify_failed = self._verify_resolved_master_data(
            valid_histories, mappings
        )

        if not valid_histories:
            # 全被复核拦下:没有可推的发票。
            result = ImportResult(total=len(histories))
            result.failed = preflight_failed + verify_failed
            result.elapsed_ms = int((time.time() - t0) * 1000)
            return result

        xlsx_bytes = mrerp_xlsx_generator.generate_xlsx(
            valid_histories, mappings, sheet_kind="sales_credit"
        )

        expected_invoices = [
            mrerp_xlsx_generator.derive_mrerp_invoice_no(h) for h in valid_histories
        ]

        # Upload runs UN-retried: MR.ERP enforces uniqueness on invoice_no,
        # so a retried POST after a slow first call produces a duplicate
        # rejection on the second attempt while the first quietly wrote.
        # Post-confirm timeouts fall through to listing verification.
        kind, payload = self._upload_and_fetch_report(
            xlsx_bytes,
            expected_invoices=expected_invoices,
        )

        if kind == "report":
            evidence = self._shot("report-captured", "report.php xlsx parsed")
            report = parse_import_report(payload)  # type: ignore[arg-type]
            result = self._classify_against_inputs(
                valid_histories,
                report,
                evidence_screenshot=evidence,
            )
            if self.screenshot_dir and payload:
                report_save = self.screenshot_dir / f"report-{int(time.time())}.xlsx"
                try:
                    report_save.write_bytes(payload)
                    result.report_xlsx_path = str(report_save)
                except OSError:
                    pass
        elif kind == "all_success":
            # importpc.php returned "1" — every row committed; no report.
            evidence = self._shot("all-success", "importpc=1 (no report generated)")
            result = ImportResult(total=len(valid_histories))
            for h, inv in zip(valid_histories, expected_invoices):
                result.success.append(
                    SuccessRow(
                        invoice_no=inv,
                        mrerp_bill_no=f"SI{inv}",
                        original=h,
                    )
                )
        else:  # "listing_verified"
            evidence = self._shot(
                "listing-verified",
                "post-confirm timeout fallback to listing",
            )
            result = self._classify_via_listing(
                valid_histories,
                expected_invoices,
                evidence_screenshot=evidence,
            )

        # Merge preflight + fail-safe verify failures into the final result.
        if preflight_failed:
            result.failed.extend(preflight_failed)
        if verify_failed:
            result.failed.extend(verify_failed)
        result.total = len(histories)  # full input count, not just valid
        result.elapsed_ms = int((time.time() - t0) * 1000)
        result.xlsx_size_bytes = len(xlsx_bytes)
        return result

    def _any_invoice_in_listing(self, invoices: List[str]) -> bool:
        """Listing-verification helper for the download-timeout fallback.

        Cheap probe: just check whether any expected bill_no string appears
        anywhere in the listing HTML. Faster than running search_invoice
        per row because we only need a yes/no for the fallback decision.
        """
        try:
            list_url = (
                f"{self.login_url}{self.SC_PATH_LISTING}" f"?idmenu={self.listing_idmenu}&mode=l"
            )
            self._page.goto(
                list_url,
                wait_until="networkidle",
                timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
            )
            html = self._page.content() or ""
        except Exception as e:
            logger.warning("listing fallback navigation failed: %s", e)
            return False
        return any((f"SI{inv}" in html) or (inv in html) for inv in invoices)

    def _classify_via_listing(
        self,
        histories: List[Dict[str, Any]],
        expected_invoices: List[str],
        evidence_screenshot: Optional[str],
    ) -> ImportResult:
        """Build an ImportResult by polling the listing instead of parsing
        the report xlsx. Used when the download event missed (MR.ERP's
        first-call latency can stretch past the download budget while still
        writing rows server-side).

        Limitation vs. report parsing: per-row failure reasons are lost.
        Rows present in listing -> SuccessRow. Rows absent -> FailedRow
        with a generic "uncertain" reason so the caller can ask the user
        to retry only the missing rows.
        """
        result = ImportResult(total=len(histories))
        by_invoice: Dict[str, Dict[str, Any]] = {}
        for h, inv in zip(histories, expected_invoices):
            by_invoice[inv] = h

        try:
            list_url = (
                f"{self.login_url}{self.SC_PATH_LISTING}" f"?idmenu={self.listing_idmenu}&mode=l"
            )
            self._page.goto(
                list_url,
                wait_until="networkidle",
                timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
            )
            html = self._page.content() or ""
        except Exception as e:
            logger.warning("listing classification nav failed: %s", e)
            html = ""

        for inv, original in by_invoice.items():
            if (f"SI{inv}" in html) or (inv in html):
                result.success.append(
                    SuccessRow(
                        invoice_no=inv,
                        mrerp_bill_no=f"SI{inv}",
                        original=original,
                    )
                )
            else:
                reasons = [
                    "import status uncertain: report.php download "
                    "did not arrive and listing does not contain "
                    "this invoice",
                ]
                result.failed.append(
                    FailedRow(
                        invoice_no=inv,
                        reasons=reasons,
                        reasons_friendly=translate_reasons(reasons),
                        original=original,
                        evidence_screenshot=evidence_screenshot,
                    )
                )
        return result

    def _classify_against_inputs(
        self,
        histories: List[Dict[str, Any]],
        report: ImportReport,
        evidence_screenshot: Optional[str],
    ) -> ImportResult:
        """Cross-reference parsed report rows back to the input histories.

        MR.ERP rewrites our invoice_no when generating bill_no (`SI` + ours)
        but echoes the original in the report's first column. We match by
        the exact `invoice_no` string we sent.
        """
        by_invoice: Dict[str, Dict[str, Any]] = {}
        for h in histories:
            inv = mrerp_xlsx_generator.derive_mrerp_invoice_no(h)
            by_invoice[inv] = h

        result = ImportResult(total=len(histories))

        for inv in report.success:
            original = by_invoice.get(inv, {})
            result.success.append(
                SuccessRow(
                    invoice_no=inv,
                    mrerp_bill_no=f"SI{inv}",
                    original=original,
                )
            )
        for row in report.failed:
            original = by_invoice.get(row.invoice_no, {})
            reasons = list(row.reasons)
            result.failed.append(
                FailedRow(
                    invoice_no=row.invoice_no,
                    reasons=reasons,
                    reasons_friendly=translate_reasons(reasons),
                    original=original,
                    evidence_screenshot=evidence_screenshot,
                )
            )

        # Inputs that didn't appear in the report at all (shouldn't happen
        # under §9 semantics but defend anyway).
        seen = {s.invoice_no for s in result.success} | {f.invoice_no for f in result.failed}
        for inv, original in by_invoice.items():
            if inv not in seen:
                reasons = ["report did not mention this invoice"]
                result.failed.append(
                    FailedRow(
                        invoice_no=inv,
                        reasons=reasons,
                        reasons_friendly=translate_reasons(reasons),
                        original=original,
                        evidence_screenshot=evidence_screenshot,
                    )
                )
        return result

    # ----- search ----------------------------------------------------

    def search_invoice(self, invoice_no: str) -> Optional[InvoiceRecord]:
        """Find the listing row whose bill_no contains our invoice_no.

        Returns None if not present. Used both for confirmation after an
        upload and as a precursor to delete_invoice.
        """
        self.select_company()

        def attempt() -> Optional[InvoiceRecord]:
            page = self._page
            list_url = (
                f"{self.login_url}{self.SC_PATH_LISTING}" f"?idmenu={self.listing_idmenu}&mode=l"
            )
            try:
                page.goto(list_url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            except (PWTimeout, PWError) as e:
                raise MRERPTechnicalError(f"listing nav timeout: {e}") from e

            if self._is_login_bounced():
                self._logged_in = self._company_selected = False
                raise MRERPAuthError("session expired before listing")

            try:
                html = page.content() or ""
            except Exception as e:
                raise MRERPTechnicalError(f"listing content() failed: {e}") from e

            bill_no = f"SI{invoice_no}"
            # listing rows look like
            #   <p><span>SIPEARNLY-TEST-001</span>...<a href="allform.php?id=N&...status=del">
            row_re = re.compile(
                r"<p\b[^>]*>(?:(?!</p>).){0,3000}"
                + re.escape(bill_no)
                + r'(?:(?!</p>).){0,3000}allform\.php\?id=(\d+)&[^"]*status=del',
                re.DOTALL,
            )
            m = row_re.search(html)
            if not m:
                # fallback for embedding variations
                fb_re = re.compile(
                    re.escape(invoice_no) + r'.{0,2000}allform\.php\?id=(\d+)&[^"]*status=del',
                    re.DOTALL,
                )
                m = fb_re.search(html)
            if not m:
                return None

            return InvoiceRecord(
                invoice_no=invoice_no,
                bill_no=bill_no,
                db_row_id=m.group(1),
                listing_url=page.url,
            )

        return self._retry_technical(attempt, "search_invoice")

    # ----- delete ----------------------------------------------------

    def delete_invoice(self, db_row_id: str) -> bool:
        """Click through the 2-step delete flow for one row. Returns True
        if the row is gone from the listing afterwards."""
        if not db_row_id or not str(db_row_id).isdigit():
            raise ValueError(f"db_row_id must be a numeric string, " f"got {db_row_id!r}")
        self.select_company()
        return self._retry_technical(
            lambda: self._delete_once(str(db_row_id)),
            "delete_invoice",
        )

    def _delete_once(self, db_row_id: str) -> bool:
        page = self._page
        del_form_url = f"{self.login_url}{self.SC_PATH_FORM}" f"?id={db_row_id}&status=del"
        try:
            page.goto(del_form_url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"delete form nav timeout: {e}") from e

        if self._is_login_bounced():
            self._logged_in = self._company_selected = False
            raise MRERPAuthError("session expired before delete")

        btn = page.locator('button[id="btndel"]')
        if btn.count() == 0:
            self._shot("delete-btn-missing", f"db_row_id={db_row_id} has no btndel")
            raise MRERPTechnicalError(f"delete form for id={db_row_id} has no btndel button")

        try:
            btn.first.click(timeout=5_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"btndel click timeout: {e}") from e

        # The confirmdel() JS pops a confirm dialog; the global handler
        # accepts it. The server then POSTs and bounces us back to allview.
        page.wait_for_timeout(3_000)
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except PWTimeout:
            pass
        self._shot("after-delete", f"URL={page.url}")

        # Verification: re-fetch listing and ensure the bill_no is gone.
        list_url = f"{self.login_url}{self.SC_PATH_LISTING}" f"?idmenu={self.listing_idmenu}&mode=l"
        try:
            page.goto(list_url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"post-delete listing verification timeout: {e}") from e
        html = page.content() or ""
        still_there = f"allform.php?id={db_row_id}" in html
        self._shot(
            "verify-deletion",
            "ok" if not still_there else f"row {db_row_id} still listed",
        )
        return not still_there
