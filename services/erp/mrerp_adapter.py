# -*- coding: utf-8 -*-
"""
services/erp/mrerp_adapter.py

Production MR.ERP integration adapter.

Lineage:
    - Probe scaffold:  scripts/probe/probe-mrerp.py (10/10 end-to-end ok
                       on 2026-05-18, run_id 20260518-193925)
    - Site facts:      docs/integrations/mrerp-known-facts.md
    - xlsx contract:   docs/integrations/mrerp-spec.md §4-§6

Architecture rules this module obeys (CLAUDE.md/CLAUDE.md):
    §7  Playwright only — never speak HTTP to mrerp4sme.com directly.
    §8  xlsx generation goes through mrerp_xlsx_generator.generate_xlsx,
        which already clones the verified Korn template byte-for-byte.
    §9  importpc.php returning "2" does NOT mean DB write succeeded.
        Truth comes from report.php's xlsx (parsed by mrerp_report_parser).

Public surface:
    class MRERPAdapter:
        # construction
        __init__(*, login_url, username, password,
                 comidyear='6', seldb='1',
                 idmenu_sales_credit='370', selmenu_sales_credit='118',
                 headless=True, screenshot_dir=None,
                 retry_attempts=3, retry_base_delay=1.0,
                 retry_max_delay=30.0)
        @classmethod from_encrypted(...)        # decrypts via kms_helper

        # lifecycle
        __enter__ / __exit__                    # owns the browser session

        # business
        login() -> None                         # idempotent
        select_company() -> None                # idempotent; auto-logs in
        upload_invoice_batch(histories,
                             mappings) -> ImportResult
        search_invoice(invoice_no) -> Optional[InvoiceRecord]
        delete_invoice(db_row_id) -> bool

Exception taxonomy (see services.erp.exceptions):
    MRERPAuthError       — credentials bounced; do NOT retry
    MRERPTechnicalError  — timeout / 5xx / missing selector; RETRY
    MRERPBusinessError   — server accepted but rejected rows; do NOT retry

Dataclass returns: InvoiceRecord, ImportResult, FailedRow.
"""

from __future__ import annotations

import logging
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from playwright.sync_api import (
    Error as PWError,
    Page,
    TimeoutError as PWTimeout,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mrerp_xlsx_generator                              # noqa: E402
from services.erp._browser import BrowserSession        # noqa: E402
from services.erp.exceptions import (                   # noqa: E402
    MRERPAuthError,
    MRERPBusinessError,
    MRERPError,
    MRERPTechnicalError,
)
from services.erp.mrerp_business_friendly import (      # noqa: E402
    translate_reasons,
)
from services.erp.mrerp_report_parser import (          # noqa: E402
    ImportReport,
    parse_import_report,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================
# Result dataclasses
# ============================================================

@dataclass
class InvoiceRecord:
    """One row found via search_invoice()."""
    invoice_no: str
    bill_no: str
    db_row_id: str
    listing_url: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FailedRow:
    """One invoice that failed business validation.

    `reasons` holds the raw Thai/English text exactly as MR.ERP wrote it
    in the report.xlsx (or our ERR_* code for preflight failures).
    `reasons_friendly` is a parallel list of `{lang: translation}` dicts
    sourced from `services.erp.mrerp_business_friendly`; the UI picks
    whichever language matches the viewer."""
    invoice_no: str
    reasons: List[str]
    original: Dict[str, Any]
    reasons_friendly: List[Dict[str, str]] = field(default_factory=list)
    evidence_screenshot: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SuccessRow:
    """One invoice that landed in MR.ERP's DB."""
    invoice_no: str
    mrerp_bill_no: str
    original: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImportResult:
    """Return value of upload_invoice_batch."""
    total: int
    success: List[SuccessRow] = field(default_factory=list)
    failed: List[FailedRow] = field(default_factory=list)
    elapsed_ms: int = 0
    xlsx_size_bytes: int = 0
    report_xlsx_path: Optional[str] = None

    @property
    def all_success(self) -> bool:
        return self.total > 0 and not self.failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "success": [s.to_dict() for s in self.success],
            "failed": [f.to_dict() for f in self.failed],
            "elapsed_ms": self.elapsed_ms,
            "xlsx_size_bytes": self.xlsx_size_bytes,
            "report_xlsx_path": self.report_xlsx_path,
            "all_success": self.all_success,
        }


# ============================================================
# The adapter
# ============================================================

class MRERPAdapter:

    SC_PATH_FORMUPLOAD = "/impartran/formupload.php"
    SC_PATH_FORMRDPC = "/impartran/formrdpc.php"
    SC_PATH_LISTING = "/artran/allview.php"
    SC_PATH_FORM = "/artran/allform.php"
    LOGIN_PATH = "/login/login.php"
    SELECTDB_PATH = "/login/selectdb.php"
    MAINMENU_PATH = "/login/mainmenu.php"

    UPLOAD_TIMEOUT_MS = 20_000
    PREVIEW_TIMEOUT_MS = 20_000
    REPORT_DOWNLOAD_TIMEOUT_MS = 120_000   # PHP first-call warmup can run >60s
    DEFAULT_PAGE_TIMEOUT_MS = 15_000

    def __init__(
        self,
        *,
        login_url: str,
        username: str,
        password: str,
        comidyear: str = "6",
        seldb: str = "1",
        idmenu_sales_credit: str = "370",
        selmenu_sales_credit: str = "118",
        listing_idmenu: str = "118",
        headless: bool = True,
        screenshot_dir: Optional[Path] = None,
        retry_attempts: int = 3,
        retry_delays_seconds: Tuple[float, ...] = (1.0, 5.0, 30.0),
        slow_mo_ms: int = 0,
    ):
        if not login_url:
            raise ValueError("login_url required")
        if not username or not password:
            raise ValueError("username and password required")

        self.login_url = login_url.rstrip("/")
        self._username = username
        self._password = password
        self.comidyear = str(comidyear)
        self.seldb = str(seldb)
        self.idmenu_sc = str(idmenu_sales_credit)
        self.selmenu_sc = str(selmenu_sales_credit)
        self.listing_idmenu = str(listing_idmenu)
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        self.retry_attempts = max(1, int(retry_attempts))
        self.retry_delays = tuple(retry_delays_seconds)
        self.slow_mo_ms = max(0, int(slow_mo_ms))

        self._session: Optional[BrowserSession] = None
        self._logged_in = False
        self._company_selected = False

    # ----- construction helpers --------------------------------------

    @classmethod
    def from_encrypted(
        cls,
        *,
        login_url: str,
        encrypted_username: str,
        encrypted_password: str,
        **kwargs,
    ) -> "MRERPAdapter":
        """Build an adapter from Fernet-encrypted credentials.

        Decryption uses services-wide kms_helper (`PEARNLY_KMS_KEY` env).
        The plaintext only lives in this adapter's memory; nothing logs it.
        """
        from kms_helper import decrypt_str   # import here so unit tests
                                              # that don't need encryption
                                              # don't require PEARNLY_KMS_KEY
        return cls(
            login_url=login_url,
            username=decrypt_str(encrypted_username),
            password=decrypt_str(encrypted_password),
            **kwargs,
        )

    # ----- context lifecycle -----------------------------------------

    def __enter__(self) -> "MRERPAdapter":
        secrets = [self._password]
        if len(self._username) >= 3:
            secrets.append(self._username)
        self._session = BrowserSession(
            headless=self.headless,
            screenshot_dir=self.screenshot_dir,
            redact_strings=secrets,
            slow_mo_ms=self.slow_mo_ms,
        ).__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._session is not None:
            self._session.__exit__(exc_type, exc, tb)
        self._session = None
        self._logged_in = False
        self._company_selected = False

    # ----- internals --------------------------------------------------

    @property
    def _page(self) -> Page:
        if self._session is None:
            raise RuntimeError("MRERPAdapter used outside `with` block")
        return self._session.page

    def _shot(self, name: str, scenario: str = "") -> Optional[str]:
        if not self._session:
            return None
        p = self._session.screenshot(name, scenario)
        return str(p) if p else None

    def _retry_technical(self, fn: Callable[[], T], op_name: str) -> T:
        """Execute fn, retrying on MRERPTechnicalError with the configured
        delay schedule. MRERPAuthError and MRERPBusinessError pass through
        immediately (not retryable by contract)."""
        last: Optional[MRERPTechnicalError] = None
        for attempt in range(1, self.retry_attempts + 1):
            try:
                return fn()
            except MRERPTechnicalError as e:
                last = e
                if attempt < self.retry_attempts:
                    delay = self._delay_for_attempt(attempt)
                    logger.warning(
                        "%s technical failure (attempt %d/%d): %s; "
                        "sleeping %.1fs",
                        op_name, attempt, self.retry_attempts, e, delay,
                    )
                    time.sleep(delay)
        assert last is not None
        logger.error("%s failed after %d attempts: %s",
                     op_name, self.retry_attempts, last)
        raise last

    def _delay_for_attempt(self, attempt: int) -> float:
        """attempt is 1-indexed; returns the delay AFTER this attempt before
        the next one. retry_delays_seconds is sampled by index."""
        idx = attempt - 1
        if idx < len(self.retry_delays):
            return float(self.retry_delays[idx])
        return float(self.retry_delays[-1]) if self.retry_delays else 1.0

    # ----- login -----------------------------------------------------

    def login(self) -> None:
        """Idempotent. Lands on /login/login.php, fills credentials, asserts
        we end up somewhere protected (selectdb / mainmenu)."""
        if self._logged_in:
            return
        self._retry_technical(self._login_once, "login")
        self._logged_in = True

    def _login_once(self) -> None:
        page = self._page

        # Step 1: warm-up GET. Old PHP needs a session cookie before any POST.
        try:
            page.goto(self.login_url + "/",
                      wait_until="domcontentloaded",
                      timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"landing GET timeout: {e}") from e

        # Navigate to the login form. The landing page is marketing copy;
        # the real form lives at /login/login.php. Click the anchor if
        # present, otherwise direct nav.
        try:
            link = page.locator('a[href*="login.php"], a[href*="/login/"]').first
            if link.count() > 0:
                try:
                    link.click(timeout=5_000)
                except Exception:
                    page.goto(self.login_url + self.LOGIN_PATH,
                              wait_until="networkidle",
                              timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            else:
                page.goto(self.login_url + self.LOGIN_PATH,
                          wait_until="networkidle",
                          timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"nav to login form timeout: {e}") from e

        self._shot("login-page", f"URL={page.url}")

        # Fill and submit.
        try:
            user_in = page.locator('input[name="txtusers"]')
            pass_in = page.locator('input[name="txtpasswords"]')
            if user_in.count() == 0 or pass_in.count() == 0:
                raise MRERPTechnicalError(
                    "login form missing txtusers/txtpasswords inputs")
            user_in.first.fill(self._username)
            pass_in.first.fill(self._password)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"login form fill timeout: {e}") from e

        # Click submit (multiple fallbacks for selector evolution).
        clicked = False
        for sel in (
            'input[name="btnsubmit"]',
            'input[type="submit"]',
            'button[type="submit"]',
            'button:has-text("Submit")',
        ):
            btn = page.locator(sel)
            if btn.count() > 0:
                try:
                    btn.first.click(timeout=5_000)
                    clicked = True
                    break
                except Exception:
                    continue
        if not clicked:
            try:
                page.locator('input[name="txtpasswords"]').first.press("Enter")
            except Exception as e:
                raise MRERPTechnicalError(
                    f"no submit selector matched and Enter fallback failed: {e}"
                ) from e

        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except PWTimeout:
            pass

        self._shot("post-login", f"URL={page.url}")

        # Auth verdict. MR.ERP returns 200 + login form HTML on failure
        # (no 302), so URL + body inspection is required.
        if self._is_login_bounced():
            self._shot("login-bounced", f"URL={page.url}")
            raise MRERPAuthError(
                f"login bounced back to public area; URL={page.url}")

        # Double-check: try selectdb.php. If that bounces too, definite fail.
        try:
            page.goto(self.login_url + self.SELECTDB_PATH,
                      wait_until="networkidle",
                      timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"selectdb verification timeout: {e}") from e

        if ("login.php" in page.url.lower()
                and "selectdb" not in page.url.lower()):
            self._shot("login-bounced-selectdb", f"URL={page.url}")
            raise MRERPAuthError(
                f"selectdb requires login; URL={page.url}")

        self._shot("login-ok", f"URL={page.url}")
        logger.info("login ok; landed at %s", page.url)

    def _is_login_bounced(self) -> bool:
        page = self._page
        url_low = page.url.lower()
        try:
            body_html = (page.content() or "")[:8000].lower()
        except Exception:
            body_html = ""
        try:
            body_text = page.locator("body").inner_text(timeout=2_000) or ""
        except Exception:
            body_text = ""

        # Failure signal: we're on a public URL AND the body looks like the
        # login form, AND we don't see a logout link.
        public_urls = ("checklogin", "/login/index", "/login/?", "/login.php")
        looks_public = any(kw in url_low for kw in public_urls)
        # Marketing root is also "public" for our purposes.
        if (url_low.rstrip("/").endswith("/index.php")
                or url_low.rstrip("/").endswith("mrerp4sme.com")):
            looks_public = True

        login_form_in_body = (
            "txtusers" in body_html or "txtpasswords" in body_html
        )
        has_logout = ("ออกจากระบบ" in body_text or "logout" in body_html)
        protected_url = any(
            kw in url_low
            for kw in ("selectdb", "mainmenu", "impartran", "imparse", "armas")
        )

        if has_logout or protected_url:
            return False
        return looks_public and (login_form_in_body
                                  or "เข้าสู่ระบบ" in body_text)

    # ----- select company --------------------------------------------

    def select_company(self) -> None:
        """Idempotent. Ensures we're inside the configured company DB."""
        if self._company_selected:
            return
        self.login()
        self._retry_technical(self._select_company_once, "select_company")
        self._company_selected = True

    def _select_company_once(self) -> None:
        page = self._page
        target = (
            f"{self.login_url}{self.MAINMENU_PATH}"
            f"?comidyear={self.comidyear}&seldb={self.seldb}"
        )
        try:
            page.goto(target,
                      wait_until="networkidle",
                      timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"company selection nav timeout: {e}") from e

        if self._is_login_bounced():
            # Session evaporated between login and select_company.
            self._logged_in = False
            raise MRERPAuthError(
                f"company selection bounced to login; URL={page.url}")

        self._shot("company-selected",
                   f"comidyear={self.comidyear} seldb={self.seldb}")

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

        self.select_company()
        t0 = time.time()

        # P1-A §3.1-§3.5 · client-side preflight before touching the
        # browser. Rejects field-length overflow, negative amount,
        # invalid tax kind, far-future dates etc. up front so we don't
        # waste an upload round-trip (and so the user sees the real
        # root cause instead of MR.ERP's "length too long" mask).
        preflight_failed: List[FailedRow] = []
        valid_histories: List[Dict[str, Any]] = []
        for h in histories:
            ok, err_code, warnings = (
                mrerp_xlsx_generator.validate_history_for_sales_credit(
                    h, mappings,
                )
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
                if h.get("invoice_date") else
                (h.get("invoice_number") or h.get("invoice_no") or "?")
            )
            reasons = [err_code or "ERR_UNKNOWN_PREFLIGHT"]
            preflight_failed.append(FailedRow(
                invoice_no=inv_no,
                reasons=reasons,
                reasons_friendly=translate_reasons(reasons),
                original=h,
            ))

        if not valid_histories:
            # Every history was rejected at preflight; nothing to upload.
            result = ImportResult(total=len(histories))
            result.failed = preflight_failed
            result.elapsed_ms = int((time.time() - t0) * 1000)
            return result

        xlsx_bytes = mrerp_xlsx_generator.generate_xlsx(
            valid_histories, mappings, sheet_kind="sales_credit"
        )

        expected_invoices = [
            mrerp_xlsx_generator.derive_mrerp_invoice_no(h)
            for h in valid_histories
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
            evidence = self._shot(
                "report-captured", "report.php xlsx parsed"
            )
            report = parse_import_report(payload)   # type: ignore[arg-type]
            result = self._classify_against_inputs(
                valid_histories, report, evidence_screenshot=evidence,
            )
            if self.screenshot_dir and payload:
                report_save = (
                    self.screenshot_dir / f"report-{int(time.time())}.xlsx"
                )
                try:
                    report_save.write_bytes(payload)
                    result.report_xlsx_path = str(report_save)
                except OSError:
                    pass
        elif kind == "all_success":
            # importpc.php returned "1" — every row committed; no report.
            evidence = self._shot(
                "all-success", "importpc=1 (no report generated)"
            )
            result = ImportResult(total=len(valid_histories))
            for h, inv in zip(valid_histories, expected_invoices):
                result.success.append(SuccessRow(
                    invoice_no=inv,
                    mrerp_bill_no=f"SI{inv}",
                    original=h,
                ))
        else:  # "listing_verified"
            evidence = self._shot(
                "listing-verified",
                "post-confirm timeout fallback to listing",
            )
            result = self._classify_via_listing(
                valid_histories, expected_invoices,
                evidence_screenshot=evidence,
            )

        # Merge preflight failures into the final result.
        if preflight_failed:
            result.failed.extend(preflight_failed)
        result.total = len(histories)   # full input count, not just valid
        result.elapsed_ms = int((time.time() - t0) * 1000)
        result.xlsx_size_bytes = len(xlsx_bytes)
        return result

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
        upload_url = (
            f"{self.login_url}{self.SC_PATH_FORMUPLOAD}"
            f"?idmenu={self.idmenu_sc}"
        )
        try:
            page.goto(upload_url,
                      wait_until="networkidle",
                      timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"formupload nav timeout: {e}") from e

        if self._is_login_bounced():
            self._logged_in = self._company_selected = False
            raise MRERPAuthError("session expired before upload")

        # Step B: write xlsx bytes to a temp file (set_input_files requires
        # a path) and feed it to the file input.
        import tempfile
        with tempfile.NamedTemporaryFile(
            suffix=".xlsx", delete=False
        ) as tmp:
            tmp.write(xlsx_bytes)
            tmp_path = tmp.name

        try:
            file_in = page.locator(
                'input[type="file"], input[name="uploadfile"]'
            )
            if file_in.count() == 0:
                raise MRERPTechnicalError(
                    "upload form missing file input element")
            try:
                file_in.first.set_input_files(tmp_path)
            except (PWTimeout, PWError) as e:
                raise MRERPTechnicalError(
                    f"set_input_files timeout: {e}") from e
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
                    page.evaluate(
                        "typeof frmupload === 'function' && frmupload()"
                    )
                except Exception as e:
                    raise MRERPTechnicalError(
                        f"upload button missing and JS fallback "
                        f"failed: {e}") from e
            else:
                try:
                    upload_btn.first.click(timeout=5_000)
                except (PWTimeout, PWError) as e:
                    raise MRERPTechnicalError(
                        f"upload click timeout: {e}") from e

            # Wait for AJAX to settle and the navigation to fire.
            dialogs_before = len(self._session.dialogs) if self._session else 0
            try:
                page.wait_for_url("**/formrdpc.php**",
                                  timeout=self.UPLOAD_TIMEOUT_MS)
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
                raise MRERPTechnicalError(
                    f"upload did not navigate to formrdpc; URL={page.url}")
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
                    'font[color="red"], span[style*="red"], '
                    '.error, .alert'
                ).all():
                    t = (el.inner_text() or "").strip()
                    if t and len(t) < 300:
                        red_msgs.append(t)
            except Exception:
                pass
            raise MRERPBusinessError(
                f"preview shows 0 importable rows; "
                f"hints={red_msgs or 'none'}",
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
            raise MRERPTechnicalError(
                "preview has rows but no frmimport form")

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
                    logger.warning(
                        "could not read importpc.php body: %s", e
                    )
                    importpc_body = ""
            elif (
                "report.php" in url
                and report_response_body is None
            ):
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
                raise MRERPTechnicalError(
                    f"uploadfrm({fid}) raised: {e}") from e

        # Phase 1: wait for importpc to reply (it tells us the branch).
        importpc_deadline = time.time() + (
            self.REPORT_DOWNLOAD_TIMEOUT_MS / 1000.0
        )
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
                f"importpc.php silent after "
                f"{self.REPORT_DOWNLOAD_TIMEOUT_MS}ms",
            )
            if self._any_invoice_in_listing(expected_invoices):
                return "listing_verified", None
            raise MRERPTechnicalError(
                f"importpc.php did not respond within "
                f"{self.REPORT_DOWNLOAD_TIMEOUT_MS}ms and no expected "
                f"invoice appears in listing")

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
                f"({body[:200]!r}); no fallback listing match")

        # Phase 2: importpc said "2" - wait for the report. Either:
        #   - download event fires (attachment), or
        #   - inline response body fires (rare; some builds may serve
        #     the xlsx without Content-Disposition).
        report_deadline = time.time() + 60.0
        while (
            not downloads
            and report_response_body is None
            and time.time() < report_deadline
        ):
            try:
                page.wait_for_timeout(250)
            except Exception:
                time.sleep(0.25)

        report_bytes_captured: Optional[bytes] = None

        if downloads:
            d = downloads[0]
            try:
                dl_path = d.path()   # blocks until download completes
                if dl_path:
                    report_bytes_captured = Path(dl_path).read_bytes()
            except Exception as e:
                logger.warning("download.path()/read failed: %s", e)

        if (
            report_bytes_captured is None
            and report_response_body is not None
        ):
            report_bytes_captured = report_response_body

        if report_bytes_captured is None:
            self._shot(
                "report-response-missed",
                "importpc returned '2' but no report download nor "
                "inline body within 60s",
            )
            if self._any_invoice_in_listing(expected_invoices):
                return "listing_verified", None
            raise MRERPTechnicalError(
                "importpc.php returned '2' but neither a download "
                "event nor a report.php response arrived within 60s "
                "and no expected invoice appears in listing")

        if not report_bytes_captured:
            self._shot(
                "report-empty-body",
                "report.php capture was empty",
            )
            if self._any_invoice_in_listing(expected_invoices):
                return "listing_verified", None
            raise MRERPTechnicalError("report.php capture is empty")

        if report_bytes_captured[:2] != b"PK":
            preview = report_bytes_captured[:200].decode(
                "utf-8", errors="replace"
            )
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
                "report.php returned non-xlsx body and no expected "
                "invoice appears in listing")

        return "report", report_bytes_captured

    def _any_invoice_in_listing(self, invoices: List[str]) -> bool:
        """Listing-verification helper for the download-timeout fallback.

        Cheap probe: just check whether any expected bill_no string appears
        anywhere in the listing HTML. Faster than running search_invoice
        per row because we only need a yes/no for the fallback decision.
        """
        try:
            list_url = (
                f"{self.login_url}{self.SC_PATH_LISTING}"
                f"?idmenu={self.listing_idmenu}&mode=l"
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
                f"{self.login_url}{self.SC_PATH_LISTING}"
                f"?idmenu={self.listing_idmenu}&mode=l"
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
                result.success.append(SuccessRow(
                    invoice_no=inv,
                    mrerp_bill_no=f"SI{inv}",
                    original=original,
                ))
            else:
                reasons = [
                    "import status uncertain: report.php download "
                    "did not arrive and listing does not contain "
                    "this invoice",
                ]
                result.failed.append(FailedRow(
                    invoice_no=inv,
                    reasons=reasons,
                    reasons_friendly=translate_reasons(reasons),
                    original=original,
                    evidence_screenshot=evidence_screenshot,
                ))
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
            result.success.append(SuccessRow(
                invoice_no=inv,
                mrerp_bill_no=f"SI{inv}",
                original=original,
            ))
        for row in report.failed:
            original = by_invoice.get(row.invoice_no, {})
            reasons = list(row.reasons)
            result.failed.append(FailedRow(
                invoice_no=row.invoice_no,
                reasons=reasons,
                reasons_friendly=translate_reasons(reasons),
                original=original,
                evidence_screenshot=evidence_screenshot,
            ))

        # Inputs that didn't appear in the report at all (shouldn't happen
        # under §9 semantics but defend anyway).
        seen = {s.invoice_no for s in result.success} | \
               {f.invoice_no for f in result.failed}
        for inv, original in by_invoice.items():
            if inv not in seen:
                reasons = ["report did not mention this invoice"]
                result.failed.append(FailedRow(
                    invoice_no=inv,
                    reasons=reasons,
                    reasons_friendly=translate_reasons(reasons),
                    original=original,
                    evidence_screenshot=evidence_screenshot,
                ))
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
                f"{self.login_url}{self.SC_PATH_LISTING}"
                f"?idmenu={self.listing_idmenu}&mode=l"
            )
            try:
                page.goto(list_url,
                          wait_until="networkidle",
                          timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            except (PWTimeout, PWError) as e:
                raise MRERPTechnicalError(
                    f"listing nav timeout: {e}") from e

            if self._is_login_bounced():
                self._logged_in = self._company_selected = False
                raise MRERPAuthError("session expired before listing")

            try:
                html = page.content() or ""
            except Exception as e:
                raise MRERPTechnicalError(
                    f"listing content() failed: {e}") from e

            bill_no = f"SI{invoice_no}"
            # listing rows look like
            #   <p><span>SIPEARNLY-TEST-001</span>...<a href="allform.php?id=N&...status=del">
            row_re = re.compile(
                r'<p\b[^>]*>(?:(?!</p>).){0,3000}'
                + re.escape(bill_no)
                + r'(?:(?!</p>).){0,3000}allform\.php\?id=(\d+)&[^"]*status=del',
                re.DOTALL,
            )
            m = row_re.search(html)
            if not m:
                # fallback for embedding variations
                fb_re = re.compile(
                    re.escape(invoice_no)
                    + r'.{0,2000}allform\.php\?id=(\d+)&[^"]*status=del',
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
            raise ValueError(f"db_row_id must be a numeric string, "
                             f"got {db_row_id!r}")
        self.select_company()
        return self._retry_technical(
            lambda: self._delete_once(str(db_row_id)),
            "delete_invoice",
        )

    def _delete_once(self, db_row_id: str) -> bool:
        page = self._page
        del_form_url = (
            f"{self.login_url}{self.SC_PATH_FORM}"
            f"?id={db_row_id}&status=del"
        )
        try:
            page.goto(del_form_url,
                      wait_until="networkidle",
                      timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"delete form nav timeout: {e}") from e

        if self._is_login_bounced():
            self._logged_in = self._company_selected = False
            raise MRERPAuthError("session expired before delete")

        btn = page.locator('button[id="btndel"]')
        if btn.count() == 0:
            self._shot("delete-btn-missing",
                       f"db_row_id={db_row_id} has no btndel")
            raise MRERPTechnicalError(
                f"delete form for id={db_row_id} has no btndel button")

        try:
            btn.first.click(timeout=5_000)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"btndel click timeout: {e}") from e

        # The confirmdel() JS pops a confirm dialog; the global handler
        # accepts it. The server then POSTs and bounces us back to allview.
        page.wait_for_timeout(3_000)
        try:
            page.wait_for_load_state("networkidle", timeout=8_000)
        except PWTimeout:
            pass
        self._shot("after-delete", f"URL={page.url}")

        # Verification: re-fetch listing and ensure the bill_no is gone.
        list_url = (
            f"{self.login_url}{self.SC_PATH_LISTING}"
            f"?idmenu={self.listing_idmenu}&mode=l"
        )
        try:
            page.goto(list_url,
                      wait_until="networkidle",
                      timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(
                f"post-delete listing verification timeout: {e}") from e
        html = page.content() or ""
        still_there = f"allform.php?id={db_row_id}" in html
        self._shot(
            "verify-deletion",
            "ok" if not still_there else f"row {db_row_id} still listed",
        )
        return not still_there

    # ----- diagnostics -----------------------------------------------

    def dialog_log(self) -> List[str]:
        """Return a snapshot of JS dialog messages captured since the
        session started. Useful for surfacing alert() text in error
        responses without giving callers access to the live Playwright
        page."""
        return self._session.dialogs if self._session else []


__all__ = [
    "MRERPAdapter",
    "InvoiceRecord",
    "ImportResult",
    "SuccessRow",
    "FailedRow",
    "MRERPError",
    "MRERPAuthError",
    "MRERPTechnicalError",
    "MRERPBusinessError",
    "parse_import_report",
]
