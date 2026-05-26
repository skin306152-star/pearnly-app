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

import mrerp_xlsx_generator  # noqa: E402
from services.erp._browser import BrowserSession  # noqa: E402
from services.erp.session_lock import mrerp_session_lock  # noqa: E402
from services.erp.exceptions import (  # noqa: E402
    MRERPAuthError,
    MRERPBusinessError,
    MRERPError,
    MRERPTechnicalError,
)
from services.erp.mrerp_business_friendly import (  # noqa: E402
    translate_reasons,
)
from services.erp.mrerp_report_parser import (  # noqa: E402
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
    REPORT_DOWNLOAD_TIMEOUT_MS = 120_000  # PHP first-call warmup can run >60s
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
        enable_master_data_sync: bool = False,
        master_data_auto_create: bool = False,
        seed_customer_code: Optional[str] = None,
        seed_product_code: Optional[str] = None,
        generic_product_code: Optional[str] = None,
        serialize_sessions: bool = True,
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
        # P1-B Phase 5: master-data sync wiring.
        # `enable_master_data_sync=True` makes upload_invoice_batch enrich
        # `mappings.clients` via MRERPCustomerSyncService.lookup BEFORE
        # generating the xlsx, so an OCR buyer_name maps to an existing
        # MR.ERP customer_code without the caller having to pre-stitch.
        # `master_data_auto_create=True` extends the same preflight to
        # call lookup_or_create (copy-from-seed; see
        # mrerp_customer_sync._layer4_auto_create + the
        # mrerp-customer-copy-flow.md doc). Requires
        # `seed_customer_code` to be set or the call raises
        # MRERPBusinessError(ERR_NO_SEED_CUSTOMER).
        # `seed_customer_code` — existing MR.ERP customer code (e.g.
        # "0006") whose master-data references the new auto-created
        # rows inherit. Set this from `endpoint.config.seed_customer_code`
        # on the persisted MR.ERP connection.
        self.enable_master_data_sync = bool(enable_master_data_sync)
        self.master_data_auto_create = bool(master_data_auto_create)
        self.seed_customer_code = (seed_customer_code or "").strip() or None
        self.seed_product_code = (seed_product_code or "").strip() or None
        # P1「开箱即用」(Zihao 2026-05-26 拍板) · 通用商品码兜底模式。
        # 配了 generic_product_code = 进入「匹配优先 + 通用兜底 · 不自动建商品」:
        #   - 商品行能对上 ERP 已有真实商品 → 用真码(精准)。
        #   - 对不上(定制长描述) → 挂这个通用销售商品码,OCR 行描述原样保留
        #     在行名/备注。**不再逐行去 ERP 现场建商品**(慢+脏+撞码+截断的根)。
        # 不配(None) = 精确模式 = 老行为完全不变(保护现有付费用户)。
        # 注意:这只 gate 商品;买方仍按 master_data_auto_create 自动建(真实主体)。
        self.generic_product_code = (generic_product_code or "").strip() or None
        self._customer_sync = None  # lazy-created on first use
        self._product_sync = None  # lazy-created on first use

        # 2026-05-25 · 跨进程会话串行锁(治 worker 互踢 ERR_AUTH)。
        # 老 PHP 单账号单会话 · 2 worker 同推同账号会互踢 · 见 session_lock.py。
        self.serialize_sessions = bool(serialize_sessions)
        self._lock_cm = None

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
        from kms_helper import decrypt_str  # import here so unit tests

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
        # 先拿账号级跨进程串行锁(在开浏览器之前 · 不持浏览器空等锁)·
        # 同一 MR.ERP 账号同一刻只允许一个会话登录 · 避免老 PHP 互踢 ERR_AUTH。
        if self.serialize_sessions:
            self._lock_cm = mrerp_session_lock(f"{self.login_url}|{self._username}")
            try:
                self._lock_cm.__enter__()
            except Exception:
                # 锁基础设施异常不应阻断推送 · 降级放行
                self._lock_cm = None
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
        # 释放会话锁(浏览器关闭后再放锁 · 确保整段操作期间独占账号)
        if self._lock_cm is not None:
            try:
                self._lock_cm.__exit__(exc_type, exc, tb)
            finally:
                self._lock_cm = None

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
                        "%s technical failure (attempt %d/%d): %s; " "sleeping %.1fs",
                        op_name,
                        attempt,
                        self.retry_attempts,
                        e,
                        delay,
                    )
                    time.sleep(delay)
        assert last is not None
        logger.error("%s failed after %d attempts: %s", op_name, self.retry_attempts, last)
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
            page.goto(
                self.login_url + "/",
                wait_until="domcontentloaded",
                timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
            )
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
                    page.goto(
                        self.login_url + self.LOGIN_PATH,
                        wait_until="networkidle",
                        timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
                    )
            else:
                page.goto(
                    self.login_url + self.LOGIN_PATH,
                    wait_until="networkidle",
                    timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
                )
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"nav to login form timeout: {e}") from e

        self._shot("login-page", f"URL={page.url}")

        # v118.34.15 (Zihao 2026-05-19 拍板) · login form discovery hardening.
        # Previously: looked up input[name="txtusers"] immediately after
        # nav with no wait. On slow networks or when MR.ERP is mid-deploy
        # the form HTML isn't in the DOM yet, count()==0 raises
        # "login form missing txtusers/txtpasswords inputs" — which is
        # what the user reported on production after one successful run.
        #
        # New flow:
        #   1. wait_for_selector with primary + fallback selectors,
        #      total 15 s budget
        #   2. on timeout: detect maintenance page (Thai keywords +
        #      "maintenance" English) and raise a more specific error
        #   3. on timeout (not maintenance): reload + wait again, 15 s
        #   4. still nothing: save full-page screenshot to /tmp and
        #      include the path in the error so /api/version's
        #      last_500 traceback carries actionable context
        user_in, pass_in = self._wait_for_login_inputs_with_retry()
        try:
            user_in.fill(self._username)
            pass_in.fill(self._password)
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
            raise MRERPAuthError(f"login bounced back to public area; URL={page.url}")

        # Double-check: try selectdb.php. If that bounces too, definite fail.
        try:
            page.goto(
                self.login_url + self.SELECTDB_PATH,
                wait_until="networkidle",
                timeout=self.DEFAULT_PAGE_TIMEOUT_MS,
            )
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"selectdb verification timeout: {e}") from e

        if "login.php" in page.url.lower() and "selectdb" not in page.url.lower():
            self._shot("login-bounced-selectdb", f"URL={page.url}")
            raise MRERPAuthError(f"selectdb requires login; URL={page.url}")

        self._shot("login-ok", f"URL={page.url}")
        logger.info("login ok; landed at %s", page.url)

    # v118.34.15 (Zihao 2026-05-19 拍板) · login form robustness ──────
    # 主 + fallback 选择器 · 顺序按"最常见 → 最宽松"。MR.ERP 历史里
    # 用户名 input name 一直是 txtusers · 但 id / type 偶尔变 · fallback
    # 用 id*='user' 兜底,实在不行就最后扫 input[type='text']:visible。
    _LOGIN_USER_SELECTORS = (
        'input[name="txtusers"]',
        'input[name="txtuser"]',
        'input[id="txtusers"]',
        'input[id*="user" i]:not([type="hidden"])',
        'input[type="text"]:visible',
    )
    _LOGIN_PASS_SELECTORS = (
        'input[name="txtpasswords"]',
        'input[name="txtpassword"]',
        'input[name="password"]',
        'input[id="txtpasswords"]',
        'input[type="password"]:visible',
    )

    # Maintenance keywords drawn from MR.ERP's actual outage pages
    # (Thai operator messages) plus generic English fallbacks. Hit
    # detection early so we raise a specific "MR.ERP under maintenance"
    # message instead of the generic technical error.
    _MAINTENANCE_HINTS = (
        "ปิดปรับปรุง",  # under maintenance (Thai)
        "ปรับปรุงระบบ",  # system upgrade (Thai)
        "อยู่ระหว่างปรับปรุง",  # currently being upgraded
        "under maintenance",
        "scheduled maintenance",
        "system upgrade in progress",
        "503 service unavailable",
    )

    def _detect_maintenance_page(self) -> Optional[str]:
        """Return a maintenance-hint string if the page body matches one
        of the known maintenance signatures, else None. Called when
        login form selectors time out — distinguishes 'MR.ERP is down'
        from 'our selector is wrong' so we can surface a friendlier
        error to the wizard."""
        page = self._page
        try:
            body_text = (page.locator("body").inner_text(timeout=2_000) or "").lower()
        except Exception:
            body_text = ""
        for hint in self._MAINTENANCE_HINTS:
            if hint.lower() in body_text:
                return hint
        return None

    def _try_locate_login_inputs(self, *, timeout_ms: int):
        """Probe the user + password locators in order. Returns
        (user_locator_first, pass_locator_first) on success, or
        (None, None) if neither pair resolved within budget. Budget is
        split across the selectors so a flaky first selector doesn't
        starve fallbacks."""
        page = self._page
        per_selector_ms = max(800, timeout_ms // max(1, len(self._LOGIN_USER_SELECTORS)))

        user_loc = None
        for sel in self._LOGIN_USER_SELECTORS:
            try:
                page.wait_for_selector(sel, timeout=per_selector_ms, state="attached")
                loc = page.locator(sel).first
                if loc.count() > 0:
                    user_loc = loc
                    break
            except (PWTimeout, PWError):
                continue
        if user_loc is None:
            return None, None

        pass_loc = None
        for sel in self._LOGIN_PASS_SELECTORS:
            try:
                page.wait_for_selector(sel, timeout=per_selector_ms, state="attached")
                loc = page.locator(sel).first
                if loc.count() > 0:
                    pass_loc = loc
                    break
            except (PWTimeout, PWError):
                continue
        if pass_loc is None:
            return None, None
        return user_loc, pass_loc

    def _save_login_fail_screenshot(self) -> Optional[str]:
        """Always-on screenshot to /tmp/ when the form lookup gives up.
        Independent of self.screenshot_dir (which is unset for the
        wizard's test-connection path). Path is returned so the error
        message includes it."""
        import time as _time

        try:
            path = f"/tmp/mrerp_login_fail_{int(_time.time())}.png"
            self._page.screenshot(path=path, full_page=True)
            return path
        except Exception as e:
            logger.warning("save_login_fail_screenshot failed: %s", e)
            return None

    def save_listing_fail_screenshot(self, kind: str = "listing") -> Optional[str]:
        """A3 (Zihao 2026-05-19 拍板) · listing fetch failure screenshot.
        Parallel to _save_login_fail_screenshot. Public method so the
        customer/product sync services can call it through the adapter
        reference they already hold (`self.adapter`).

        `kind` typically 'customers' / 'products' — embedded in the
        filename so support can grep the right file.
        """
        import time as _time

        if self._page is None:
            return None
        try:
            safe_kind = "".join(c for c in kind if c.isalnum() or c in "._-") or "listing"
            path = f"/tmp/mrerp_listing_fail_{safe_kind}_{int(_time.time())}.png"
            self._page.screenshot(path=path, full_page=True)
            return path
        except Exception as e:
            logger.warning("save_listing_fail_screenshot failed: %s", e)
            return None

    def _wait_for_login_inputs_with_retry(self):
        """Returns (user_locator, pass_locator) once both are visible.
        Strategy:
          1. 15 s budget on the page as-is.
          2. If timeout: detect maintenance page → specific error.
          3. Otherwise: page.reload() + another 15 s budget.
          4. Still nothing: save screenshot to /tmp, raise
             MRERPTechnicalError with the path baked in so
             /api/version's last_500 carries it forward.
        """
        page = self._page
        # Try 1
        user_in, pass_in = self._try_locate_login_inputs(timeout_ms=15_000)
        if user_in is not None and pass_in is not None:
            return user_in, pass_in

        # Possible maintenance — check before the costly reload.
        hint = self._detect_maintenance_page()
        if hint:
            self._shot("login-maintenance", f"hint={hint}")
            shot_path = self._save_login_fail_screenshot()
            raise MRERPTechnicalError(
                f"MR.ERP appears to be under maintenance "
                f"(hint='{hint}' on URL={page.url}); screenshot={shot_path}"
            )

        # Try 2 — reload the page once.
        logger.info(
            "login form not found on first probe — reloading %s and retrying",
            page.url,
        )
        try:
            page.reload(wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            shot_path = self._save_login_fail_screenshot()
            raise MRERPTechnicalError(
                f"login page reload failed: {e}; screenshot={shot_path}"
            ) from e

        user_in, pass_in = self._try_locate_login_inputs(timeout_ms=15_000)
        if user_in is not None and pass_in is not None:
            return user_in, pass_in

        # Final maintenance check on the reloaded page.
        hint = self._detect_maintenance_page()
        if hint:
            self._shot("login-maintenance-after-reload", f"hint={hint}")
            shot_path = self._save_login_fail_screenshot()
            raise MRERPTechnicalError(
                f"MR.ERP appears to be under maintenance after reload "
                f"(hint='{hint}'); screenshot={shot_path}"
            )

        # Give up. Save screenshot so future debugging has visual context.
        shot_path = self._save_login_fail_screenshot()
        raise MRERPTechnicalError(
            f"login form missing txtusers/txtpasswords inputs after reload; "
            f"URL={page.url}; screenshot={shot_path}"
        )

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
        if url_low.rstrip("/").endswith("/index.php") or url_low.rstrip("/").endswith(
            "mrerp4sme.com"
        ):
            looks_public = True

        login_form_in_body = "txtusers" in body_html or "txtpasswords" in body_html
        has_logout = "ออกจากระบบ" in body_text or "logout" in body_html
        protected_url = any(
            kw in url_low for kw in ("selectdb", "mainmenu", "impartran", "imparse", "armas")
        )

        if has_logout or protected_url:
            return False
        return looks_public and (login_form_in_body or "เข้าสู่ระบบ" in body_text)

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
            page.goto(target, wait_until="networkidle", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
        except (PWTimeout, PWError) as e:
            raise MRERPTechnicalError(f"company selection nav timeout: {e}") from e

        if self._is_login_bounced():
            # Session evaporated between login and select_company.
            self._logged_in = False
            raise MRERPAuthError(f"company selection bounced to login; URL={page.url}")

        self._shot("company-selected", f"comidyear={self.comidyear} seldb={self.seldb}")

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
        import mrerp_xlsx_generator as _gen

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

    @staticmethod
    def _extract_items(history: Dict[str, Any]):
        """Pull product line-items out of a flat OCR history dict.

        OCR shape examples handled:
          history['items']              flat list at top level
          history['fields']['items']    nested under fields (common)
          history['pages'][i]['fields']['items']    multi-page invoices

        Returns a list of ItemInfo, deduped by normalized item_name.
        """
        from services.erp.mrerp_product_sync import ItemInfo
        from services.erp._matching import normalize_item_name

        f = history.get("fields") if isinstance(history, dict) else {}
        f = f if isinstance(f, dict) else {}
        candidates = []
        for src in (
            history.get("items"),
            f.get("items"),
        ):
            if isinstance(src, list) and src:
                candidates = src
                break
        if not candidates and isinstance(history.get("pages"), list):
            for p in history["pages"]:
                if not isinstance(p, dict):
                    continue
                pf = p.get("fields") or {}
                if isinstance(pf, dict) and isinstance(pf.get("items"), list):
                    candidates = pf["items"]
                    break

        seen_norm = set()
        items = []
        tenant_id = str(history.get("tenant_id") or "")
        for it in candidates:
            if not isinstance(it, dict):
                continue
            name = it.get("name") or it.get("description") or it.get("item_name") or ""
            name = str(name or "").strip()
            if not name:
                continue
            norm = normalize_item_name(name)
            if norm in seen_norm:
                continue
            seen_norm.add(norm)
            items.append(
                ItemInfo(
                    name=name,
                    tenant_id=tenant_id,
                    unit_code=(it.get("unit") or it.get("unit_code") or None),
                    client_id=int(history.get("client_id") or 0),
                )
            )
        return items

    @staticmethod
    def _extract_buyer(history: Dict[str, Any]):
        """Pull buyer-side fields out of a flat OCR history dict.

        Importing BuyerInfo lazily so the adapter stays usable without
        the customer-sync service loaded (e.g. older callers).
        """
        from services.erp.mrerp_customer_sync import BuyerInfo

        f = history.get("fields") if isinstance(history, dict) else {}
        f = f if isinstance(f, dict) else {}
        name = history.get("buyer_name") or f.get("buyer_name") or ""
        name = str(name or "").strip()
        if not name:
            return None
        tax_id = (
            history.get("buyer_tax")
            or f.get("buyer_tax")
            or history.get("buyer_tax_id")
            or f.get("buyer_tax_id")
            or ""
        )
        addr = history.get("buyer_addr") or f.get("buyer_addr") or ""
        return BuyerInfo(
            name=name,
            client_id=int(history.get("client_id") or 0),
            tenant_id=str(history.get("tenant_id") or ""),
            tax_id=str(tax_id or "").strip() or None,
            address=str(addr or "").strip() or None,
        )

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
