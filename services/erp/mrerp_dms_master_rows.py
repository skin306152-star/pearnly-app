# -*- coding: utf-8 -*-
"""Shared parsing and memoization for MR.ERP dropdown master rows."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("services.erp.mrerp_dms_client_ops")


def memo(client: Any) -> Dict[tuple, Any]:
    """Return the per-login-session master-data memo owned by the client."""
    return client.__dict__.setdefault("_bshsd_memo", {})


def parse_rows(elemname: str, text: str) -> Optional[List[List[Any]]]:
    """Parse bshsd JSON while preserving empty-list versus fetch-failure semantics."""
    if not text.strip():
        return []
    try:
        rows = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        rows = None
    if not isinstance(rows, list):
        logger.warning(
            "[dms] bshsd %s: body is not a JSON array; treated as fetch failure", elemname
        )
        return None
    return rows
