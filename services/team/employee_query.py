# -*- coding: utf-8 -*-
"""超管用户详情使用的租户成员只读查询。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from core import db

logger = logging.getLogger("mr-pilot")


def list_employees(tenant_id: str) -> List[Dict[str, Any]]:
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, username, role, is_active, last_login_at, created_at, invited_by
                FROM users
                WHERE tenant_id = %s AND role = 'member'
                ORDER BY created_at ASC
                """,
                (str(tenant_id),),
            )
            return [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        logger.error("list_employees failed: %s", exc)
        return []
