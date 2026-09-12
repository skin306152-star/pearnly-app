# -*- coding: utf-8 -*-
"""Shared parsing, memoization and row→ref resolution for MR.ERP dropdown master rows."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from services.erp.mrerp_dms_models import DMSMasterRef

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


def row_by_id(rows: Optional[List[list]], rid: str) -> Optional[list]:
    """bshsd 主档行按 id 命中(首列即 id),取首个;没有 → None。"""
    for row in rows or []:
        if row and str(row[0]) == str(rid):
            return row
    return None


def ref_from_row(row: list) -> DMSMasterRef:
    """bshsd 行 [id, code, name, ...] → DMSMasterRef(尾列进 extra 供表单原样回显)。"""
    return DMSMasterRef(
        id=str(row[0]),
        code=str(row[1]) if len(row) > 1 else str(row[0]),
        name=str(row[2]) if len(row) > 2 else (str(row[1]) if len(row) > 1 else ""),
        extra=tuple(row[3:]),
    )
