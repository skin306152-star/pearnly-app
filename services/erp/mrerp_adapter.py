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
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from playwright.sync_api import (
    Page,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp._browser import BrowserSession  # noqa: E402
from services.erp.session_lock import mrerp_session_lock  # noqa: E402
from services.erp.exceptions import (  # noqa: E402
    MRERPAuthError,
    MRERPBusinessError,
    MRERPError,
    MRERPTechnicalError,
)
from services.erp.mrerp_report_parser import (  # noqa: E402
    parse_import_report,
)

# M0 verbatim 搬家 re-export(返回值 dataclasses → leaf · 主类 + 各 Mixin 共用 · 调用方 0 改动)
from services.erp.mrerp_adapter_models import (  # noqa: E402,F401
    FailedRow,
    ImportResult,
    InvoiceRecord,
    SuccessRow,
)

# M1/M2/M3/M4 verbatim 搬家:登录/上传/取报告/主数据方法组拆成 mixin(MRO 组合 · 0 逻辑改)
from services.erp.mrerp_adapter_login import MRERPLoginMixin  # noqa: E402
from services.erp.mrerp_adapter_upload import MRERPUploadMixin  # noqa: E402
from services.erp.mrerp_adapter_report import MRERPReportMixin  # noqa: E402
from services.erp.mrerp_adapter_masterdata import MRERPMasterDataMixin  # noqa: E402

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================
# The adapter
# ============================================================


class MRERPAdapter(MRERPLoginMixin, MRERPUploadMixin, MRERPReportMixin, MRERPMasterDataMixin):

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
        from core.kms_helper import decrypt_str  # import here so unit tests

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
