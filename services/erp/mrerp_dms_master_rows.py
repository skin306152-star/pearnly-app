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
    """Parse bshsd JSON while preserving empty-list versus fetch-failure semantics.

    生产协议(2026-09-13 同会话只读原始响应勘查,租户 bshsd):
      · 已登录、该目录 0 行 → HTTP 200 且**空正文**(0 字节,如本租户的四类付款银行目录);
        空正文就是合法的空目录,必须解析成 [] —— 不是"没读到"。
      · 未登录/认证失效 → HTTP 200 但正文是 65 字节非 JSON(非数组)→ None,fail closed。
    故只有 **非 JSON 正文**(HTML/错误页/非数组/对象/null)才算取数失败;空正文按空表处理。
    """
    if not text.strip():
        # 空正文 = DMS 此租户「该目录 0 行」的合法形态,不是取数失败;认证失败走下面的非 JSON 分支。
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
