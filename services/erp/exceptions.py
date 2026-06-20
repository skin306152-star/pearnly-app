# -*- coding: utf-8 -*-
"""
services/erp/exceptions.py

Exception hierarchy for ERP adapters (MR.ERP first; other adapters later).

Modeled on services/ocr/layer1_vision.py so the upstream push pipeline can
dispatch identically across pipelines.

Catch MRERPError for any MR.ERP adapter failure. Use subclasses to decide:
- MRERPAuthError       => stop, notify user to reconfigure credentials
- MRERPTechnicalError  => retry with exponential backoff
- MRERPBusinessError   => return failure to caller; user must fix invoice data
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class MRERPError(Exception):
    """Base exception for all MR.ERP adapter failures."""


class MRERPAuthError(MRERPError):
    """Credentials invalid / session revoked / login bounced back to public area.

    NOT retryable. The user must update the encrypted credentials in
    erp_endpoints (or wherever the adapter pulls them from).
    """


class MRERPTechnicalError(MRERPError):
    """Network timeout, Playwright wait_for_url timeout, formrdpc.php 500,
    selector unexpectedly missing, etc.

    Retryable. Upstream should retry with exponential backoff (1s / 5s / 30s).
    """


class MRERPBusinessError(MRERPError):
    """Server accepted the upload but rejected one or more rows for business
    reasons (customer code missing, duplicate invoice number, product not
    found, ...).

    NOT retryable: retrying the same xlsx produces the same rejection. The
    caller receives the structured `failed` list from ImportResult so the
    user can correct the source data and retry.
    """

    def __init__(
        self,
        message: str,
        failed_rows: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(message)
        self.failed_rows = failed_rows or []
