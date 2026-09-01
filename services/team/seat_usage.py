# -*- coding: utf-8 -*-
"""租户席位计量。"""

from __future__ import annotations

from typing import Dict

from core import db


def seat_usage(tenant_id: str) -> Dict[str, int]:
    """返回活跃成员和已占席位数。"""
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS members FROM memberships "
            "WHERE tenant_id = %s AND status = 'active'",
            (str(tenant_id),),
        )
        row = cur.fetchone() or {}
    members = int(row.get("members") or 0)
    return {"members": members, "used": members}
