# -*- coding: utf-8 -*-
"""
services/erp/_browser.py

Internal Playwright session helper for MR.ERP adapters.

Encapsulates the boilerplate that probe-mrerp.py established as working:
- launch chromium (headed or headless)
- new context with locale=th-TH, viewport 1440x900
- inject init script that hooks `sdpt()` (MR.ERP's custom navigator)
  so target="_blank" pop-ups become same-tab navigations -> Playwright
  can observe them
- global page.on("dialog") handler that accepts every JS confirm/alert
  and captures the message text for inspection
- credential-stripping log filter so passwords never appear in logs
- screenshot helper that auto-numbers files

Public surface:
    BrowserSession(headless, viewport, screenshot_dir, redact_strings)
        - .__enter__ / .__exit__
        - .page                 # the live page
        - .dialogs              # list[str] of captured dialog messages
        - .last_dialog          # most recent dialog message or ""
        - .screenshot(name, scenario="")  -> Path
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

logger = logging.getLogger(__name__)


SDPT_INIT_SCRIPT = """
(function() {
    var patched = false;
    function tryPatch() {
        if (patched) return;
        if (typeof window.sdpt === 'function') {
            var orig = window.sdpt;
            window.sdpt = function(objval, actionval, targetval) {
                console.log('SDPT_PATCHED', actionval);
                return orig(objval, actionval, '_self');
            };
            patched = true;
        }
    }
    if (document.readyState === 'complete') tryPatch();
    else {
        window.addEventListener('load', tryPatch);
        document.addEventListener('DOMContentLoaded', tryPatch);
    }
    setTimeout(tryPatch, 200);
    setTimeout(tryPatch, 800);
})();
"""


class _RedactFilter(logging.Filter):
    """Replace literal credential substrings (passwords, session tokens) with
    '***' before the record reaches any handler. Filters are mutable so the
    caller can update redactions after construction."""

    def __init__(self, redactions: Optional[List[str]] = None):
        super().__init__()
        self.redactions: List[str] = [r for r in (redactions or []) if r]

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.redactions:
            return True
        try:
            msg = record.getMessage()
        except Exception:
            return True
        replaced = msg
        changed = False
        for token in self.redactions:
            if token and token in replaced:
                replaced = replaced.replace(token, "***")
                changed = True
        if changed:
            record.msg = replaced
            record.args = None
        return True


def install_redact_filter(
    log: logging.Logger,
    secrets: List[str],
) -> _RedactFilter:
    """Attach a redaction filter to the given logger. Idempotent: replacing
    an existing filter avoids duplicate scrubbing."""
    for existing in list(log.filters):
        if isinstance(existing, _RedactFilter):
            log.removeFilter(existing)
    f = _RedactFilter(secrets)
    log.addFilter(f)
    return f


@dataclass
class BrowserSession:
    """Context manager that owns one Playwright browser + context + page.

    Use as:
        with BrowserSession(headless=True, screenshot_dir=Path("...")) as bs:
            bs.page.goto(...)
            bs.screenshot("login-ok")
    """

    headless: bool = True
    viewport_width: int = 1440
    viewport_height: int = 900
    locale: str = "th-TH"
    slow_mo_ms: int = 0
    screenshot_dir: Optional[Path] = None
    redact_strings: List[str] = field(default_factory=list)

    # Populated on __enter__:
    _pw: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _ctx: Optional[BrowserContext] = None
    _page: Optional[Page] = None
    _dialogs: List[str] = field(default_factory=list)
    _shot_count: int = 0

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("BrowserSession used outside `with` block")
        return self._page

    @property
    def dialogs(self) -> List[str]:
        return list(self._dialogs)

    @property
    def last_dialog(self) -> str:
        return self._dialogs[-1] if self._dialogs else ""

    def __enter__(self) -> "BrowserSession":
        install_redact_filter(logger, self.redact_strings)
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo_ms,
        )
        self._ctx = self._browser.new_context(
            viewport={"width": self.viewport_width,
                      "height": self.viewport_height},
            locale=self.locale,
            accept_downloads=True,
        )
        self._ctx.add_init_script(SDPT_INIT_SCRIPT)
        self._page = self._ctx.new_page()
        self._page.on("dialog", self._on_dialog)
        if self.screenshot_dir:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        for closer in (self._ctx, self._browser):
            if closer is not None:
                try:
                    closer.close()
                except Exception:
                    pass
        if self._pw is not None:
            try:
                self._pw.stop()
            except Exception:
                pass
        self._ctx = self._browser = self._page = self._pw = None

    def _on_dialog(self, dialog) -> None:
        msg = (dialog.message or "")[:500]
        self._dialogs.append(f"[{dialog.type}] {msg}")
        logger.info("dialog (%s): %s", dialog.type, msg)
        try:
            dialog.accept()
        except Exception:
            pass

    def screenshot(self, name: str, scenario: str = "") -> Optional[Path]:
        if not self.screenshot_dir or self._page is None:
            return None
        self._shot_count += 1
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-") or "shot"
        ts = time.strftime("%H%M%S")
        fname = f"{self._shot_count:02d}-{ts}-{slug}.png"
        path = self.screenshot_dir / fname
        try:
            self._page.screenshot(path=str(path), full_page=True)
        except Exception as e:
            logger.warning("screenshot %s failed: %s", fname, e)
            return None
        if scenario:
            logger.info("shot %s | %s", fname, scenario)
        return path
