# -*- coding: utf-8 -*-
"""
mrerp_adapter_login.py · MRERPAdapter 登录 / 选公司 Mixin

从 mrerp_adapter.py 抽出（REFACTOR-WB-modularize M1 · verbatim 搬家 0 逻辑改）。
方法体一字未改;`self.X` 经 MRO 解析回主类 MRERPAdapter（构造态 + class 常量 + 其它 mixin
方法）。主类 `class MRERPAdapter(MRERPLoginMixin, MRERPUploadMixin, MRERPMasterDataMixin)` 多继承组合。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, TypeVar

from playwright.sync_api import (
    Error as PWError,
    TimeoutError as PWTimeout,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.exceptions import (  # noqa: E402
    MRERPAuthError,
    MRERPTechnicalError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MRERPLoginMixin:
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
