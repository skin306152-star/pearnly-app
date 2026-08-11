# -*- coding: utf-8 -*-
"""销售顾问归属(提成算给谁)的选项与钉死写入 —— 花名册里的例外通道。

默认由 services/erp/dms_advisor 自动匹配(DMS 登录名 ↔ 员工表 ↔ 顾问下拉)。老板代录、
账号压根不在顾问名册时自动匹配必然落空,出路是在该操作员端点的
config.booking_defaults.advisor_id/advisor_name 上钉死归属(钉死优先于一切匹配)。

选项取老板端点的主档缓存(dms_masters_cache),顾问行形 [id, code, name, tel] —— 只外露
前三列,tel 是员工私人号码,下拉用不上。名字一律服务端按 id 重解:客户端能改的 name 直接
决定月底提成表上印谁,不能信。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mr-pilot")

_COL_CODE = 1
_COL_NAME = 2


def _cell(row: list, idx: int) -> str:
    if not row or len(row) <= idx or row[idx] is None:
        return ""
    return str(row[idx]).strip()


def list_options(endpoint: Dict[str, Any]) -> Optional[List[Dict[str, str]]]:
    """老板端点的顾问选项;取数失败 → None。

    None 与空表是两件事:名册真的没人 → 前端给空态指路,取数失败 → 前端给可重试的错态。
    先读已暖的缓存,miss 才触发一次登录冷抓(缓存 12h,开一次弹窗抓一次不划算)。
    """
    from services.erp import dms_masters_cache

    try:
        masters = dms_masters_cache.read_fresh_masters(endpoint)
        if masters is None:
            masters = dms_masters_cache.get_masters(endpoint)
    except Exception:
        logger.warning("[dms_roster] load advisors failed", exc_info=True)
        return None
    if not masters:
        return None  # get_masters 登录失败时软回退成空 dict —— 当取数失败报,不冒充空名册
    return [
        {"id": _cell(r, 0), "code": _cell(r, _COL_CODE), "name": _cell(r, _COL_NAME)}
        for r in masters.get("advisors") or []
        if _cell(r, 0)
    ]


def pick(options: Optional[List[Dict[str, str]]], advisor_id: str) -> Optional[Dict[str, str]]:
    """id → {"id", "name"};不在名册 → None(不放行客户端塞来的任意 id)。"""
    needle = str(advisor_id or "").strip()
    for opt in options or []:
        if opt.get("id") == needle:
            return {"id": opt["id"], "name": opt.get("name") or ""}
    return None


def merge_into_config(config: Dict[str, Any], advisor: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """把钉死并进端点 config(advisor=None → 清除,回到自动匹配)。

    booking_defaults 按键改写、不整包替换:同一个 dict 里还住着向导写的 booking_prefix 等键,
    整包覆盖会把它们静默吞掉(erp_endpoints PATCH 防丢层同坑)。
    """
    cfg = dict(config or {})
    defaults = dict(cfg.get("booking_defaults") or {})
    if advisor is None:
        defaults.pop("advisor_id", None)
        defaults.pop("advisor_name", None)
    else:
        defaults["advisor_id"] = advisor["id"]
        defaults["advisor_name"] = advisor["name"]
    if defaults:
        cfg["booking_defaults"] = defaults
    else:
        cfg.pop("booking_defaults", None)
    return cfg
