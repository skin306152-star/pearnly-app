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


async def qa_endpoint(line_user_id: str, endpoint_id: Any) -> Optional[Dict[str, Any]]:
    """按 LINE 绑定的 user 解 DMS 端点。未绑定 / 端点被停用 → None。"""
    from services.erp import dms_id_ocr
    from services.line_dms import store

    binding = await _thr(store.get_binding_by_line_user, line_user_id)
    uid = (binding or {}).get("user_id") or ""
    if not uid:
        return None
    return await _thr(dms_id_ocr.resolve_dms_endpoint, uid, endpoint_id)


async def qa_masters(line_user_id: str, endpoint_id: Any, key: str) -> List[list]:
    """某类主档(cars/place_books/…)。端点解不出就给空表 —— 发问层据此重问,不炸会话。

    LINE 逐问每次实时拉当前 DMS:force_refresh 跳过 12h 缓存快照,当天改的主档当天可见。
    """
    ep = await qa_endpoint(line_user_id, endpoint_id)
    if not ep:
        return []
    masters = await _thr(get_masters, ep, force_refresh=True)
    return masters.get(key) or []


async def qa_paints(line_user_id: str, endpoint_id: Any, car_id: str) -> List[list]:
    """某车型的颜色主档(逐问选完车才有 car_id)。同 qa_masters:实时取,不吃 12h 缓存。

    先把同一份新抓的 masters 传给 get_paints —— 若回空 dict(强制刷新 fail closed)说明
    DMS 不可达,颜色一起诚实为空,不拿旧色冒充,也不把空 masters 写坏缓存。
    """
    if not car_id:
        return []
    ep = await qa_endpoint(line_user_id, endpoint_id)
    if not ep:
        return []
    masters = await _thr(get_masters, ep, force_refresh=True)
    if not masters:
        return []
    return (await _thr(get_paints, ep, car_id, masters)) or []
