# -*- coding: utf-8 -*-
"""booking_qa 状态机的主档/颜色同步薄壳:首读直连 DMS,成功后落 masters_synced。

两阶段同步语义(先在 booking_qa 里实现,独立成模块只为让状态机 ≤500 行):本会话首次
进主档/颜色时 force_refresh 跳过 12h 缓存直连 DMS(当天改动当天可见);拉取成功才把
qa["masters_synced"]=True 落会话;取数失败/空表不落标记,下一次仍走 live,避免把一次
瞬时失败钉死成整轮缓存。persist 由调用方注入,薄壳不依赖 booking_qa 的会话写回实现。
"""

from __future__ import annotations

from typing import List

from services.line_dms import masters_cache


async def masters(tenant_id, line_user_id, qa, key, *, persist) -> List[list]:
    """取某类主档。首次 live 拉取成功 → 落 masters_synced 并 persist,后续复用缓存。"""
    force_refresh = not qa.get("masters_synced")
    rows = await masters_cache.qa_masters(
        line_user_id, qa.get("endpoint_id"), key, force_refresh=force_refresh
    )
    if force_refresh and rows:
        qa["masters_synced"] = True
        await persist(tenant_id, line_user_id, qa)
    return rows


async def paints(tenant_id, line_user_id, qa, *, persist) -> List[list]:
    """取车型颜色,与主档共用同一把 masters_synced 开关(首次 live 成功即锁缓存)。"""
    car_id = str((qa.get("answers") or {}).get("car", {}).get("id") or "")
    force_refresh = not qa.get("masters_synced")
    rows = await masters_cache.qa_paints(
        line_user_id, qa.get("endpoint_id"), car_id, force_refresh=force_refresh
    )
    if force_refresh and rows:
        qa["masters_synced"] = True
        await persist(tenant_id, line_user_id, qa)
    return rows
