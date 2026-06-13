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
    def __init__(self, transport: Any, base_url: str):
        # base_url ends with /dms/
        self.transport = transport
        self.base_url = base_url.rstrip("/") + "/"
