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
    §8  xlsx import clones DMS' official template byte-for-byte
        (mrerp_dms_xlsx); never a regenerated workbook.
    §9  import code "sc::1" is verified by reading drfcbc back; "ep::1"
        (error report) is never treated as success.

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
    push_id_card_booking(card, defaults) -> DMSPushResult
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlsplit, urlunsplit

from services.erp._browser import BrowserSession
from services.erp.mrerp_dms_client import DMSClient, DMSClientError
from services.erp.mrerp_dms_models import BookingDefaults, DMSPushResult, ThaiIdCardPayload

logger = logging.getLogger(__name__)


class MrerpDmsAuthError(RuntimeError):
    """DMS login bounced — bad credentials / not approved. NOT retryable."""


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
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir) if screenshot_dir else None
        self.slow_mo_ms = max(0, int(slow_mo_ms))
        self._session: Optional[BrowserSession] = None
        self._logged_in = False

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
        return DMSClient(self._transport(), self.base_url)

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
        page = self._page

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
            page.fill("#txtusers", self._username)
            page.fill("#txtpasswords", self._password)

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
                        self._logged_in = True
                        return
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

    def push_id_card_booking(
        self, card: ThaiIdCardPayload, defaults: BookingDefaults
    ) -> DMSPushResult:
        """Full flow: login → resolve master refs → ensure customer →
        import booking via official template → patch identity → verify."""
        started = time.time()
        try:
            self.login()
            client = self._client()
            template = client.download_booking_template()
            booking = client.resolve_booking_payload(defaults, card)
            from services.erp.mrerp_dms_client import excel_serial
            from datetime import date, timedelta

            today = date.today()
            doc_serial = excel_serial(today)
            delivery_serial = excel_serial(today + timedelta(days=defaults.delivery_days))
            result = client.push_id_card_booking(
                card=card,
                booking=booking,
                template_bytes=template,
                doc_date_serial=doc_serial,
                delivery_date_serial=delivery_serial,
            )
            result.evidence["elapsed_ms"] = int((time.time() - started) * 1000)
            return result
        except (MrerpDmsAuthError, MrerpDmsTechnicalError) as e:
            code = "ERR_DMS_AUTH" if isinstance(e, MrerpDmsAuthError) else "ERR_DMS_TECHNICAL"
            return DMSPushResult(
                ok=False,
                error_code=code,
                error=f"{type(e).__name__}: {e}",
                evidence={"elapsed_ms": int((time.time() - started) * 1000)},
            )
        except DMSClientError as e:
            return DMSPushResult(
                ok=False,
                error_code=e.error_code,
                error=f"{type(e).__name__}: {e}",
                evidence={"elapsed_ms": int((time.time() - started) * 1000)},
            )
        except Exception as e:  # never let an unexpected error escape the push
            logger.exception("MrerpDmsAdapter.push_id_card_booking unexpected failure")
            return DMSPushResult(
                ok=False,
                error_code="ERR_DMS_UNEXPECTED",
                error=f"{type(e).__name__}: {str(e)[:300]}",
                evidence={"elapsed_ms": int((time.time() - started) * 1000)},
            )


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
