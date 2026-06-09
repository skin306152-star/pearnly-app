"""OCR HTTP 出口净化:剥离面向用户响应里的内部实现标识。

竞品可在 F12 看到 /api/ocr/recognize 响应。内部引擎名(Gemini/Vision/Typhoon 等)、
流水线层名、置信度门控、触发原因一律不出网——只留客户端真正要用的中性业务字段。
DB 留底(legacy_adapter persist 落库的 _ 前缀 debug 字段)不动,只净化 HTTP 出口。
集中一处调用,杜绝以后新加的 debug 字段再次泄漏。
"""

from __future__ import annotations

from typing import Any

# 引擎/品牌/流水线标识 key — 面向用户响应一律不出现。
_BLOCKED_KEYS = frozenset(
    {"engine", "engine_chain", "fallback_used", "typhoon_enhanced", "typhoon_pages"}
)


def strip_internal_fields(obj: Any) -> Any:
    """递归剥离:① 所有 _ 前缀 key(每页内部 debug 留底)② 引擎/品牌标识 key。
    返回净化后的新结构,不改原对象(DB 留底已在上游落库)。"""
    if isinstance(obj, dict):
        return {
            k: strip_internal_fields(v)
            for k, v in obj.items()
            if not (isinstance(k, str) and (k.startswith("_") or k in _BLOCKED_KEYS))
        }
    if isinstance(obj, list):
        return [strip_internal_fields(x) for x in obj]
    return obj
