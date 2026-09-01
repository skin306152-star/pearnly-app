# -*- coding: utf-8 -*-
"""LINE 订车会话的 DMS 主档快照。"""

from __future__ import annotations

from typing import List

from services.line_dms import masters_cache
from services.line_dms.master_contract import build_paint_snapshot, snapshot_rows


async def _snapshot(tenant_id, line_user_id, qa, *, persist):
    current = qa.get("master_snapshot")
    if current:
        return current
    current = await masters_cache.qa_snapshot(line_user_id, qa.get("endpoint_id"))
    qa["master_snapshot"] = current
    qa.pop("masters_synced", None)
    await persist(tenant_id, line_user_id, qa)
    return current


async def masters(tenant_id, line_user_id, qa, key, *, persist) -> List[list]:
    """新单首读整批抓取；同一会话所有按钮只读该版本。"""
    return snapshot_rows(
        await _snapshot(tenant_id, line_user_id, qa, persist=persist),
        key,
    )


async def paints(tenant_id, line_user_id, qa, *, persist) -> List[list]:
    """颜色按车型保存独立快照；DMS 读取失败或空表不落假快照。"""
    await _snapshot(tenant_id, line_user_id, qa, persist=persist)
    car_id = str((qa.get("answers") or {}).get("car", {}).get("id") or "")
    cached = (qa.get("paint_snapshots") or {}).get(car_id)
    if cached:
        return list(cached.get("rows") or [])
    rows = await masters_cache.qa_paints(
        line_user_id,
        qa.get("endpoint_id"),
        car_id,
        force_refresh=False,
        require_complete=True,
    )
    paint_snapshot = build_paint_snapshot(car_id, rows)
    qa.setdefault("paint_snapshots", {})[car_id] = paint_snapshot
    await persist(tenant_id, line_user_id, qa)
    return list(paint_snapshot["rows"])
