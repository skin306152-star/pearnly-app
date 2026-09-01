# -*- coding: utf-8 -*-
"""LINE 逐问的 DMS 主档取数薄壳:按 LINE 用户解端点 → 读缓存。

缓存本体是通道无关的基建,住在 services/erp/dms_masters_cache.py;本文件只做 LINE 侧那层
「会话只存 endpoint_id,取数前现解端点」的异步包装。缓存函数在这里逐名 re-export,既有
`from services.line_dms import masters_cache` 的调用方(booking_flow / booking_qa)不受搬家影响。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.erp.dms_masters_cache import (  # noqa: F401  LINE 侧沿用原命名空间
    CACHE_TTL_SECONDS,
    ensure_table,
    get_masters,
    get_paints,
    read_fresh_masters,
    refresh_from_client,
)
from services.line_dms._out import _thr
from services.line_dms.master_contract import MasterSyncError, build_snapshot


async def qa_endpoint(line_user_id: str, endpoint_id: Any) -> Optional[Dict[str, Any]]:
    """按 LINE 绑定的 user 解 DMS 端点。未绑定 / 端点被停用 → None。"""
    from services.erp import dms_id_ocr
    from services.line_dms import store

    binding = await _thr(store.get_binding_by_line_user, line_user_id)
    uid = (binding or {}).get("user_id") or ""
    if not uid:
        return None
    return await _thr(dms_id_ocr.resolve_dms_endpoint, uid, endpoint_id)


async def qa_masters(
    line_user_id: str,
    endpoint_id: Any,
    key: str,
    *,
    force_refresh: bool = False,
    require_complete: bool = False,
) -> List[list]:
    """某类主档(cars/place_books/…)。端点解不出就给空表 —— 发问层据此重问,不炸会话。

    force_refresh 只在本轮订车第一次进主档时开(当天改的主档当天可见);
    同轮后续按钮复用 12h 缓存快照,不再每步登录一遍 DMS。
    """
    ep = await qa_endpoint(line_user_id, endpoint_id)
    if not ep:
        return []
    masters = await _thr(
        get_masters,
        ep,
        force_refresh=force_refresh,
        require_complete=require_complete,
    )
    return masters.get(key) or []


async def qa_snapshot(line_user_id: str, endpoint_id: Any) -> Dict[str, Any]:
    """新订车会话的权威主档快照；失败时绝不回退旧缓存。"""
    ep = await qa_endpoint(line_user_id, endpoint_id)
    if not ep:
        raise MasterSyncError("ERR_DMS_MASTER_UNAVAILABLE", "endpoint")
    masters = await _thr(get_masters, ep, force_refresh=True, require_complete=True)
    if not masters:
        raise MasterSyncError("ERR_DMS_MASTER_UNAVAILABLE", "snapshot")
    return build_snapshot(masters)


async def qa_paints(
    line_user_id: str,
    endpoint_id: Any,
    car_id: str,
    *,
    force_refresh: bool = False,
    require_complete: bool = False,
) -> List[list]:
    """某车型的颜色主档(逐问选完车才有 car_id)。force_refresh 语义同 qa_masters。

    先把同一份 masters 传给 get_paints(force 时按 DMS 现状抓,fail closed;否则读普通缓存
    主档 + get_paints 懒加载颜色)。masters 为空(登录失败/空库)颜色一起诚实为空,
    不拿旧色冒充,也不把空 masters 写坏缓存。
    """
    if not car_id:
        return []
    ep = await qa_endpoint(line_user_id, endpoint_id)
    if not ep:
        return []
    masters = await _thr(
        get_masters,
        ep,
        force_refresh=force_refresh,
        require_complete=require_complete,
    )
    if not masters:
        if require_complete:
            raise MasterSyncError("ERR_DMS_MASTER_UNAVAILABLE", "snapshot")
        return []
    try:
        return (
            await _thr(get_paints, ep, car_id, masters, require_complete=require_complete)
        ) or []
    except Exception as exc:
        if require_complete and getattr(exc, "error_code", "") == "ERR_DMS_MASTER_UNAVAILABLE":
            raise MasterSyncError("ERR_DMS_MASTER_UNAVAILABLE", "paints") from exc
        raise
