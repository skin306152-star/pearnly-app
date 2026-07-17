# -*- coding: utf-8 -*-
"""
services/erp/mrerp_dms_client.py

Transport-agnostic DMS business client: customer ensure + booking import +
identity patch + master-data lookups against the MR.ERP DMS PHP forms.

This module speaks NO Playwright and NO requests directly. It drives an
injected `transport` object so it stays unit-testable with a fake. In
production mrerp_dms_adapter.py wraps the authenticated Playwright browser
context's request API as the transport (CLAUDE.md/CLAUDE.md §7 — the DMS
session is owned by a real Playwright browser login, not raw external HTTP).

Lineage: ported from the lab transport
    D:\\pearnly-dms-adapter-lab\\src\\dms_adapter\\client.py
which proved the form contract end-to-end (customer id 65, booking id 15,
import code sc::1) on the live DMS test tenant.

Transport protocol (duck-typed):
    transport.get(url, timeout_ms=None) -> resp
    transport.post(url, data=dict, files=dict|None, timeout_ms=None) -> resp
    resp.status_code: int
    resp.text: str
    resp.content: bytes
`files` is {field: (filename, bytes, content_type)}; `data` is a flat dict of
form fields (no repeated keys are needed by this contract).
"""

from __future__ import annotations

from typing import Any

from services.erp.mrerp_dms_client_base import (  # noqa: F401  public re-export
    DMSClientError,
    excel_serial,
    to_be_date,
    _EXCEL_EPOCH,
)
from services.erp.mrerp_dms_client_ops import DMSClientOpsMixin
from services.erp.mrerp_dms_client_forms import DMSClientFormsMixin
from services.erp.mrerp_dms_client_intake import DMSClientIntakeMixin


class DMSClient(DMSClientOpsMixin, DMSClientFormsMixin, DMSClientIntakeMixin):
    def __init__(self, transport: Any, base_url: str, *, admin_transport: Any = None):
        # base_url ends with /dms/
        self.transport = transport
        self.base_url = base_url.rstrip("/") + "/"
        # 凭据组:配了 admin(admin_transport 非 None)时,客户档写操作走它;读操作不变。
        # 可为已建好的 transport,或一个零参工厂(生产侧懒登录,避免只读也起 admin 会话)。
        self._admin_transport = admin_transport
        self._admin_transport_cached: Any = None

    def _resolve_admin_transport(self) -> Any:
        """惰性解析 admin 凭据组 transport(工厂只调一次)。未配 → None。"""
        src = self._admin_transport
        if src is None:
            return None
        if self._admin_transport_cached is None:
            self._admin_transport_cached = src() if callable(src) else src
        return self._admin_transport_cached
