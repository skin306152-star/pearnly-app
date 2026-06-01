# -*- coding: utf-8 -*-
"""
mrerp_adapter_report.py · MRERPAdapter 上传后取/解析 report.php 结果 Mixin

从 mrerp_adapter_upload.py 抽出（REFACTOR-WB-modularize M4 · verbatim 搬家 0 逻辑改）。
唯一方法 _upload_and_fetch_report —— 方法体一字未改;upload_invoice_batch 经 MRO 调
self._upload_and_fetch_report。
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple, TypeVar

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.exceptions import (  # noqa: E402
    MRERPAuthError,
    MRERPBusinessError,
    MRERPTechnicalError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MRERPReportMixin:
    def _upload_and_fetch_report(
        self,
        xlsx_bytes: bytes,
        expected_invoices: List[str],
    ) -> Tuple[str, Optional[bytes]]:
        """One attempt at the upload→preview→confirm→outcome flow.

        Returns a (kind, payload) tuple:
            ("report", xlsx_bytes)     — importpc returned "2"; report.php
                                          xlsx contains per-row หมายเหตุ
                                          rejections to parse.
            ("all_success", None)      — importpc returned "1"; every row
                                          committed cleanly so no report
                                          gets generated. Caller should
                                          synthesise SuccessRow per input.
            ("listing_verified", None) — neither importpc nor report.php
                                          response was visible to
                                          Playwright before timeout, but
                                          at least one of expected_invoices
                                          now appears in the listing.
                                          Caller should classify per-row
                                          against the listing.

        Raises:
            MRERPBusinessError   — preview empty / alert from frmupload()
                                   (server rejected the xlsx itself)
            MRERPTechnicalError  — pre-confirm failures only; post-confirm
                                   timeouts fall through to listing
                                   verification to keep the operation
                                   idempotent (MR.ERP enforces uniqueness
                                   on invoice_no, so retrying a "maybe
                                   committed" upload would duplicate).
        """
        page = self._page

        # Step A: navigate to the SC bulk-import form.
        upload_url = f"{self.login_url}{self.SC_PATH_FORMUPLOAD}" f"?idmenu={self.idmenu_sc}"
        try:
            page.goto(upload_url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"formupload nav timeout: {e}") from e

        # 最终冲刺 v118.34.30 (Zihao 2026-05-19 拍板) · 镜像 Bug 8 修法到
        # upload nav. 长 sync (listing fetch retry × 3 = 90s) 后 · MR.ERP
        # session 可能已过期 · upload nav 被 bounce 回 login.php · 抛
        # MRERPAuthError. 改:detect bounce + auto re-login + retry once ·
        # 让 push 跨过 session 真过期场景 · 不报 ERR_AUTH 给用户.
        if self._is_login_bounced():
            logger.warning("[upload] nav bounced to login · attempting re-login + retry")
            self._logged_in = False
            self._company_selected = False
            try:
                self.login()
                self.select_company()
                page.goto(
                    upload_url, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS
                )
            except Exception as e:
                raise MRERPAuthError(
                    f"upload nav session re-login failed: {type(e).__name__}: {e}"
                ) from e
            if self._is_login_bounced():
                self._logged_in = self._company_selected = False
                raise MRERPAuthError("session expired before upload (re-login did not recover)")

        # Step B: write xlsx bytes to a temp file (set_input_files requires
        # a path) and feed it to the file input.
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(xlsx_bytes)
            tmp_path = tmp.name

        try:
            file_in = page.locator('input[type="file"], input[name="uploadfile"]')
            if file_in.count() == 0:
                raise MRERPTechnicalError("upload form missing file input element")
            try:
                file_in.first.set_input_files(tmp_path)
            except (PWTimeout, PWError) as e:
                raise MRERPTechnicalError(f"set_input_files timeout: {e}") from e
            self._shot("file-chosen", f"size={len(xlsx_bytes)}B")

            # Step C: click the upload button. frmupload() fires an AJAX POST
            # to uploadexcel.php; on success it calls sdpt() to jump to
            # formrdpc.php; on failure it alerts the error.
            upload_btn = page.locator(
                'input[name="btnuploadfile"], '
                'input[onclick*="frmupload"], '
                'input[value*="อัพโหลด"], '
                'input[value*="อัปโหลด"]'
            )
            if upload_btn.count() == 0:
                # JS fallback (still browser-driven, still §7 compliant).
                try:
                    page.evaluate("typeof frmupload === 'function' && frmupload()")
                except Exception as e:
                    raise MRERPTechnicalError(
                        f"upload button missing and JS fallback " f"failed: {e}"
                    ) from e
            else:
                try:
                    upload_btn.first.click(timeout=5_000)
                except (PWTimeout, PWError) as e:
                    raise MRERPTechnicalError(f"upload click timeout: {e}") from e

            # Wait for AJAX to settle and the navigation to fire.
            dialogs_before = len(self._session.dialogs) if self._session else 0
            try:
                page.wait_for_url("**/formrdpc.php**", timeout=self.UPLOAD_TIMEOUT_MS)
            except PWTimeout:
                # If frmupload alerted an error, it lives in our dialog log.
                if self._session and len(self._session.dialogs) > dialogs_before:
                    err = self._session.dialogs[-1]
                    self._shot("upload-rejected", err[:200])
                    raise MRERPBusinessError(
                        f"server rejected upload before preview: {err}",
                        failed_rows=[],
                    )
                self._shot("upload-no-nav", f"URL={page.url}")
                raise MRERPTechnicalError(f"upload did not navigate to formrdpc; URL={page.url}")
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

        # Step D: preview page. Handle the known transient 500.
        try:
            body_head = (page.content() or "")[:1500]
        except Exception:
            body_head = ""
        if "500 Internal Server Error" in body_head:
            self._shot("preview-500", "formrdpc.php 500")
            raise MRERPTechnicalError("formrdpc.php returned 500")

        # Count import-able rows. Zero rows means the xlsx parsed but every
        # row was thrown out before reaching the report stage.
        cbs = page.locator('input[name^="cbimport["]')
        n_rows = cbs.count()
        if n_rows == 0:
            self._shot("preview-empty", "preview has 0 cbimport rows")
            # Try to surface any red-text error so the message is useful.
            red_msgs: List[str] = []
            try:
                for el in page.locator(
                    'font[color="red"], span[style*="red"], ' ".error, .alert"
                ).all():
                    t = (el.inner_text() or "").strip()
                    if t and len(t) < 300:
                        red_msgs.append(t)
            except Exception:
                pass
            raise MRERPBusinessError(
                f"preview shows 0 importable rows; " f"hints={red_msgs or 'none'}",
                failed_rows=[],
            )

        # Check every cbimport + cballfrmimport so MR.ERP knows we want
        # every row of every batch.
        for i in range(n_rows):
            try:
                cb = cbs.nth(i)
                if not cb.is_checked():
                    cb.check()
            except Exception:
                pass
        for ball in page.locator('input[name^="cballfrmimport"]').all():
            try:
                if not ball.is_checked():
                    ball.check()
            except Exception:
                pass
        self._shot("preview-checked", f"{n_rows} rows checked")

        # Step E: confirm + outcome dispatch.
        #
        # uploadfrm(N) fires an AJAX POST to importpc.php. Its body tells
        # us which branch the server took:
        #     "1" = every row committed cleanly; no report file is
        #            generated (so waiting for report.php would hang
        #            forever — caller must synthesise success).
        #     "2" = some row needed reporting; JS then calls sdpt() which
        #            POSTs to report.php and the server returns the xlsx.
        #     other = unexpected; treat as technical until we have a sample
        #            to classify it.
        #
        # We capture importpc and report.php responses via a context-level
        # listener (rather than expect_download) so the path is
        # independent of how the browser handles the report attachment.
        form_count = page.locator('form[id^="frmimport"]').count()
        if form_count == 0:
            raise MRERPTechnicalError("preview has rows but no frmimport form")

        ctx = self._session._ctx if self._session else None

        importpc_body: Optional[str] = None
        # report.php is served as an attachment (Content-Disposition:
        # attachment), so Chrome routes the response to a Download object
        # rather than buffering its body in memory. response.body() raises
        # "No resource with given identifier found" for those. Use a
        # download listener instead and keep response.body() as a fallback
        # in case some MR.ERP build serves it inline.
        downloads: List[Any] = []
        report_response_body: Optional[bytes] = None

        def _on_resp(r):
            nonlocal importpc_body, report_response_body
            try:
                url = r.url or ""
            except Exception:
                return
            if "importpc.php" in url and importpc_body is None:
                try:
                    importpc_body = (r.text() or "").strip()
                except Exception as e:
                    logger.warning("could not read importpc.php body: %s", e)
                    importpc_body = ""
            elif "report.php" in url and report_response_body is None:
                # Try the inline path; download path handled separately.
                try:
                    report_response_body = r.body()
                except Exception:
                    pass

        def _on_download(d):
            downloads.append(d)

        if ctx is not None:
            ctx.on("response", _on_resp)
        page.on("download", _on_download)

        # Fire all uploadfrm(N) invocations.
        for fid in range(1, form_count + 1):
            try:
                page.evaluate(f"uploadfrm({fid})")
            except Exception as e:
                raise MRERPTechnicalError(f"uploadfrm({fid}) raised: {e}") from e

        # Phase 1: wait for importpc to reply (it tells us the branch).
        importpc_deadline = time.time() + (self.REPORT_DOWNLOAD_TIMEOUT_MS / 1000.0)
        while importpc_body is None and time.time() < importpc_deadline:
            try:
                page.wait_for_timeout(250)
            except Exception:
                time.sleep(0.25)

        if importpc_body is None:
            # importpc never responded in our budget. Server may still
            # have written though, so check listing before bailing.
            self._shot(
                "importpc-no-response",
                f"importpc.php silent after " f"{self.REPORT_DOWNLOAD_TIMEOUT_MS}ms",
            )
            if self._any_invoice_in_listing(expected_invoices):
                return "listing_verified", None
            raise MRERPTechnicalError(
                f"importpc.php did not respond within "
                f"{self.REPORT_DOWNLOAD_TIMEOUT_MS}ms and no expected "
                f"invoice appears in listing"
            )

        body = importpc_body.strip()
        logger.info("importpc.php returned %r", body[:50])

        if body == "1":
            # All rows committed cleanly. No report is generated.
            return "all_success", None

        if body != "2":
            # Unknown response - shouldn't be normal flow.
            self._shot(
                "importpc-unexpected",
                f"importpc.php returned {body[:50]!r}",
            )
            if self._any_invoice_in_listing(expected_invoices):
                return "listing_verified", None
            raise MRERPTechnicalError(
                f"importpc.php returned unexpected body "
                f"({body[:200]!r}); no fallback listing match"
            )

        # Phase 2: importpc said "2" - wait for the report. Either:
        #   - download event fires (attachment), or
        #   - inline response body fires (rare; some builds may serve
        #     the xlsx without Content-Disposition).
        report_deadline = time.time() + 60.0
        while not downloads and report_response_body is None and time.time() < report_deadline:
            try:
                page.wait_for_timeout(250)
            except Exception:
                time.sleep(0.25)

        report_bytes_captured: Optional[bytes] = None

        if downloads:
            d = downloads[0]
            try:
                dl_path = d.path()  # blocks until download completes
                if dl_path:
                    report_bytes_captured = Path(dl_path).read_bytes()
            except Exception as e:
                logger.warning("download.path()/read failed: %s", e)

        if report_bytes_captured is None and report_response_body is not None:
            report_bytes_captured = report_response_body

        if report_bytes_captured is None:
            self._shot(
                "report-response-missed",
                "importpc returned '2' but no report download nor " "inline body within 60s",
            )
            if self._any_invoice_in_listing(expected_invoices):
                return "listing_verified", None
            raise MRERPTechnicalError(
                "importpc.php returned '2' but neither a download "
                "event nor a report.php response arrived within 60s "
                "and no expected invoice appears in listing"
            )

        if not report_bytes_captured:
            self._shot(
                "report-empty-body",
                "report.php capture was empty",
            )
            if self._any_invoice_in_listing(expected_invoices):
                return "listing_verified", None
            raise MRERPTechnicalError("report.php capture is empty")

        if report_bytes_captured[:2] != b"PK":
            preview = report_bytes_captured[:200].decode("utf-8", errors="replace")
            logger.warning(
                "report.php returned non-xlsx body (preview): %s",
                preview,
            )
            self._shot(
                "report-not-xlsx",
                "report.php returned non-xlsx (HTML?)",
            )
            if self._any_invoice_in_listing(expected_invoices):
                return "listing_verified", None
            raise MRERPTechnicalError(
                "report.php returned non-xlsx body and no expected " "invoice appears in listing"
            )

        return "report", report_bytes_captured
