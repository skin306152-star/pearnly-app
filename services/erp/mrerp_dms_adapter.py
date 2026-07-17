# -*- coding: utf-8 -*-
"""
services/erp/mrerp_dms_adapter.py

Production MR.ERP DMS (car-sales) adapter: Thai ID card → DMS customer +
booking draft.

Architecture (CLAUDE.md/CLAUDE.md):
    §7  Playwright owns the DMS session — a real chromium login, never raw
        external HTTP. After login the authenticated browser context's
        request API drives the verified DMS form contract (mrerp_dms_client),
        so business writes ride the real session cookies/origin.
    §8  Customer + 订车单 writes go through DMS' native forms; create is
        verified by reading the row back (search), never trusting the bare
        submit response. (Booking creation lives in the two-step intake path
        services/erp/erp_dms_intake.py — this adapter provides login +
        session + master-data scrape for it.)

Login flow (probed live 2026-05-31 on the DMS test tenant):
    GET  index.php → fill #txtusers / #txtpasswords → click #btnlogin →
    JS formAjax(login/checklogin.php) → on "lct::<status>::<grant>" calls
    sdpt(null,"home/home.php") (normal user) or sdpt(null,"login/selcomdb.php")
    (system owner). _browser.SDPT_INIT_SCRIPT rewrites sdpt to same-tab so
    Playwright observes the navigation.

Public surface:
    MrerpDmsAdapter(*, system_url, username, password, headless=True, ...)
    @classmethod from_encrypted(*, system_url, encrypted_username,
                                encrypted_password, **kw)
    __enter__ / __exit__        # owns the browser session
    login() -> None             # idempotent
    test_connection() -> dict   # login + master-data scrape (wizard)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

from services.erp._browser import BrowserSession
from services.erp.mrerp_dms_client import DMSClient

logger = logging.getLogger(__name__)


class MrerpDmsAuthError(RuntimeError):
    """DMS login bounced — bad credentials / not approved. NOT retryable."""


class MrerpDmsAdminAuthError(MrerpDmsAuthError):
    """The admin credential-set login bounced. Distinct from the user-session
    auth error so the route surfaces ERR_DMS_ADMIN_AUTH (admin creds wrong,
    not the user's). Subclasses MrerpDmsAuthError — catch this one first."""


class MrerpDmsTechnicalError(RuntimeError):
    """Network / Playwright / missing-selector failure. Retryable upstream."""


# ============================================================
# Playwright transport — wraps the authenticated browser context's
# request API behind the duck-typed transport DMSClient expects.
# ============================================================


class _Resp:
    __slots__ = ("status_code", "text", "content")

    def __init__(self, status_code: int, text: str, content: bytes):
        self.status_code = status_code
        self.text = text
        self.content = content


class PlaywrightTransport:
    """Drives DMS form POSTs through the logged-in Playwright context, so
    every request carries the real session cookies the browser established."""

    def __init__(self, request_context: Any):
        self._rc = request_context

    @staticmethod
    def _wrap(r) -> _Resp:
        # Decode from raw bytes leniently — binary responses (xlsx template)
        # would make Playwright's r.text() raise UnicodeDecodeError.
        body = r.body()
        return _Resp(r.status, body.decode("utf-8", "replace"), body)

    def get(self, url: str, timeout_ms: Optional[int] = None) -> _Resp:
        return self._wrap(self._rc.get(url, timeout=timeout_ms or 30000))

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout_ms: Optional[int] = None,
    ) -> _Resp:
        timeout = timeout_ms or 30000
        if files:
            multipart: Dict[str, Any] = {}
            for k, v in (data or {}).items():
                multipart[k] = str(v)
            for field, spec in files.items():
                filename, buf, content_type = spec
                multipart[field] = {"name": filename, "mimeType": content_type, "buffer": buf}
            r = self._rc.post(url, multipart=multipart, timeout=timeout)
        else:
            form = {k: str(v) for k, v in (data or {}).items()}
            r = self._rc.post(url, form=form, timeout=timeout)
        return self._wrap(r)


# ============================================================
# Adapter
# ============================================================


class MrerpDmsAdapter:
    LOGIN_TIMEOUT_MS = 20000
    DEFAULT_PAGE_TIMEOUT_MS = 15000

    def __init__(
        self,
        *,
        system_url: str,
        username: str,
        password: str,
        admin_username: Optional[str] = None,
        admin_password: Optional[str] = None,
        headless: bool = True,
        screenshot_dir: Optional[Path] = None,
        slow_mo_ms: int = 0,
    ):
        if not system_url:
            raise ValueError("system_url required")
        if not username or not password:
            raise ValueError("username and password required")
        self.login_url, self.base_url = self._normalize_urls(system_url)
        self._username = username
        self._password = password
        # 凭据组:配了 admin(两者都有)时,客户档写操作走一个独立的 admin 登录会话
        # (隔离 cookie,不动用户读会话);缺任一即无 admin,行为与单凭据逐字节一致。
        self._admin_username = (admin_username or "").strip() or None
        self._admin_password = admin_password or None
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        self.slow_mo_ms = max(0, int(slow_mo_ms))
        self._session: Optional[BrowserSession] = None
        self._logged_in = False
        self._admin_session: Optional[BrowserSession] = None
        self._admin_logged_in = False

    @property
    def has_admin_creds(self) -> bool:
        return bool(self._admin_username and self._admin_password)

    @staticmethod
    def _normalize_urls(system_url: str):
        """Return (login_url, base_url). Accepts either the full index.php URL
        or the /dms/ base. base_url ends with '/'."""
        u = system_url.strip().rstrip()
        parts = urlsplit(u)
        path = parts.path
        if path.endswith(".php"):
            login_url = u
            base_path = path.rsplit("/", 1)[0] + "/"
        else:
            base_path = path if path.endswith("/") else path + "/"
            login_url = urlunsplit((parts.scheme, parts.netloc, base_path + "index.php", "", ""))
        base_url = urlunsplit((parts.scheme, parts.netloc, base_path, "", ""))
        return login_url, base_url

    @classmethod
    def from_encrypted(
        cls,
        *,
        system_url: str,
        encrypted_username: str,
        encrypted_password: str,
        **kwargs,
    ) -> "MrerpDmsAdapter":
        """Build from Fernet-encrypted credentials (PEARNLY_KMS_KEY env).
        Plaintext only lives in this adapter's memory; nothing logs it."""
        from core.kms_helper import decrypt_str

        return cls(
            system_url=system_url,
            username=decrypt_str(encrypted_username),
            password=decrypt_str(encrypted_password),
            **kwargs,
        )

    # ----- lifecycle --------------------------------------------------

    def __enter__(self) -> "MrerpDmsAdapter":
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
        if self._admin_session is not None:
            try:
                self._admin_session.__exit__(exc_type, exc, tb)
            except Exception:
                pass
        self._admin_session = None
        self._admin_logged_in = False
        if self._session is not None:
            self._session.__exit__(exc_type, exc, tb)
        self._session = None
        self._logged_in = False

    @property
    def _page(self):
        if self._session is None:
            raise RuntimeError("MrerpDmsAdapter used outside `with` block")
        return self._session.page

    def _transport(self) -> PlaywrightTransport:
        return PlaywrightTransport(self._page.context.request)

    def _client(self) -> DMSClient:
        # 读操作走用户会话;客户档写操作在配了 admin 时懒切到 admin 会话。工厂(而非
        # 现成 transport)保证纯读路径永不起 admin 浏览器。
        admin = self._admin_writer_transport if self.has_admin_creds else None
        return DMSClient(self._transport(), self.base_url, admin_transport=admin)

    def _admin_writer_transport(self) -> PlaywrightTransport:
        """懒起 admin 会话并返回其 transport(首次写操作时触发)。"""
        self._ensure_admin_session()
        assert self._admin_session is not None  # _ensure 成功后必非空
        return PlaywrightTransport(self._admin_session.page.context.request)

    def _ensure_admin_session(self) -> None:
        """独立浏览器上下文登录 admin 凭据组(隔离 cookie,不碰用户读会话)。
        admin 登录失败 → MrerpDmsAdminAuthError(路由映射 ERR_DMS_ADMIN_AUTH)。"""
        if self._admin_logged_in:
            return
        if not self.has_admin_creds:
            raise MrerpDmsTechnicalError("admin session requested without admin credentials")
        secrets = [self._admin_password]
        if len(self._admin_username) >= 3:
            secrets.append(self._admin_username)
        self._admin_session = BrowserSession(
            headless=self.headless,
            screenshot_dir=self.screenshot_dir,
            redact_strings=secrets,
            slow_mo_ms=self.slow_mo_ms,
        ).__enter__()
        try:
            self._perform_login(
                self._admin_session.page, self._admin_username, self._admin_password
            )
        except MrerpDmsAuthError as e:
            raise MrerpDmsAdminAuthError(f"DMS admin credential login failed: {e}")
        self._admin_logged_in = True

    def session_cookies(self) -> list:
        """登录态 cookie · 供交互层缓存做只读级联提速(避免每次 dropdown 重登录)。"""
        try:
            return self._page.context.cookies()
        except Exception:
            return []

    # ----- login ------------------------------------------------------

    def login(self) -> None:
        """Idempotent. Fills credentials, clicks the JS login button, asserts
        we navigate away from index.php into the authenticated area.

        ⚠️ Timing-critical (2026-05-31 prod bug fix): index.js binds the
        #btnlogin click handler inside `window.addEventListener("load", ...)`,
        NOT on DOMContentLoaded. If we click before the `load` event fires the
        click is a silent no-op (formAjax never runs) → page stays on index.php
        → looks like an auth failure with NO rejection dialog. So we:
          1. goto with wait_until="load" (guarantees the handler is bound),
          2. retry the click a few times to absorb any residual bind race,
          3. distinguish a real DMS rejection (an alert dialog fires) from a
             timing miss (no dialog) — only the former is non-retryable.
        """
        if self._logged_in:
            return
        self._perform_login(self._page, self._username, self._password)
        self._logged_in = True

    def _perform_login(self, page, username: str, password: str) -> None:
        """Drive the timing-critical DMS login on `page` with the given creds.
        Returns on success (navigated off index.php); raises MrerpDmsAuthError
        on rejection / no completion. Holds no per-session state so both the
        user session and the admin credential-set session reuse it.
        """
        # Capture the checklogin.php verdict directly — DMS reports login
        # rejection via an in-page custom modal (bshdlal), NOT a native alert,
        # so reading the server response is the only reliable signal. Body:
        #   lct::<status>::<grant>  → status 1/2 user, 4 owner; grant 2 = not approved
        #   al::<msg> / err::<msg>  → rejected (bad creds / blocked)
        captured = {"body": None}

        def _on_resp(resp):
            try:
                if "checklogin.php" in resp.url:
                    captured["body"] = (resp.text() or "").strip()
            except Exception:
                pass

        page.on("response", _on_resp)
        try:
            page.goto(self.login_url, wait_until="load", timeout=self.DEFAULT_PAGE_TIMEOUT_MS)
            page.wait_for_selector(
                "#btnlogin", state="visible", timeout=self.DEFAULT_PAGE_TIMEOUT_MS
            )
            page.fill("#txtusers", username)
            page.fill("#txtpasswords", password)

            attempts = 3
            per_attempt_ms = max(5000, self.LOGIN_TIMEOUT_MS // attempts)
            for _attempt in range(attempts):
                captured["body"] = None
                try:
                    # Short click timeout: if the handler isn't bound yet the
                    # button is still clickable (no overlay) and returns fast;
                    # we never want to hang the default 30s here.
                    page.click("#btnlogin", timeout=5000)
                except Exception:
                    page.wait_for_timeout(600)
                    continue

                waited = 0
                while waited < per_attempt_ms:
                    if "index.php" not in page.url:
                        return  # navigated into the authenticated area
                    body = captured["body"]
                    if body:
                        self._classify_login_body(body)  # raises on rejection
                        # success verdict (lct ok) → sdpt nav is in flight; keep
                        # polling the URL until it lands.
                    page.wait_for_timeout(300)
                    waited += 300
                # No checklogin response at all this attempt = click was a
                # no-op (handler bound late). Brief buffer, then re-click.
                if not captured["body"]:
                    page.wait_for_timeout(600)
        finally:
            try:
                page.remove_listener("response", _on_resp)
            except Exception:
                pass

        raise MrerpDmsAuthError(
            "DMS login did not complete (no successful checklogin response / no "
            "navigation after retries · possible slow page load or block)."
        )

    def _classify_login_body(self, body: str) -> None:
        """Raise MrerpDmsAuthError if the checklogin.php body is a rejection.
        Returns normally for a success verdict (caller then waits for nav)."""
        parts = body.split("::")
        head = parts[0].strip().lower()
        if head == "lct":
            grant = parts[2].strip() if len(parts) > 2 else ""
            status = parts[1].strip() if len(parts) > 1 else ""
            if grant == "2":
                raise MrerpDmsAuthError("DMS account not approved for system access")
            if status == "3":
                raise MrerpDmsAuthError("DMS account is marked resigned")
            return  # status 1/2/4 = ok
        # al:: / err:: / anything else = rejected
        raise MrerpDmsAuthError(f"DMS rejected login: {body[:160]}")

    # ----- public business -------------------------------------------

    def test_connection(self) -> Dict[str, Any]:
        """Login + scrape master-data dropdowns for the connect wizard.
        Never raises — returns a structured dict the route passes to the UI."""
        t0 = time.time()
        masters = self._client().fetch_masters()
        return {
            "ok": True,
            "status": "ok",
            "message": "DMS connection ok",
            "adapter": "mrerp_dms",
            "elapsed_ms": int((time.time() - t0) * 1000),
            "defaults_required": not bool(masters.get("cars")),
            "masters": {
                "advisors": [_ref_brief(r) for r in masters.get("advisors", [])],
                "car_models": [_ref_brief(r) for r in masters.get("cars", [])],
                "place_books": [_ref_brief(r) for r in masters.get("place_books", [])],
                "term_sales": [_ref_brief(r) for r in masters.get("term_sales", [])],
                "branches": [_ref_brief(r) for r in masters.get("branches", [])],
                "regis_behalfs": [_ref_brief(r) for r in masters.get("regis_behalfs", [])],
            },
        }


def _ref_brief(row) -> Dict[str, str]:
    """bshsd row [id, code, name, ...] -> {id, code, name} for the wizard."""
    try:
        return {
            "id": str(row[0]),
            "code": str(row[1]) if len(row) > 1 else str(row[0]),
            "name": str(row[2]) if len(row) > 2 else (str(row[1]) if len(row) > 1 else ""),
        }
    except Exception:
        return {"id": "", "code": "", "name": ""}
