"""OCR HTTP 出口净化:剥离面向用户响应里的内部实现标识。

竞品可在 F12 看到 /api/ocr/recognize 响应。内部引擎名(Gemini/Vision/Typhoon 等)、
流水线层名、置信度门控、触发原因一律不出网——只留客户端真正要用的中性业务字段。
DB 留底(legacy_adapter persist 落库的 _ 前缀 debug 字段)不动,只净化 HTTP 出口。
集中一处调用,杜绝以后新加的 debug 字段再次泄漏。
"""

from __future__ import annotations

from typing import Any

# 引擎/品牌/流水线标识 + LLM 用量 key — 面向用户响应一律不出现(token 数泄漏底层用 LLM)。
_BLOCKED_KEYS = frozenset(
    {
        "api_key",
        "engine",
        "engine_chain",
        "file_hash",
        "fallback_used",
        "llm_response",
        "model",
        "model_name",
        "model_provider",
        "ocr_provider",
        "pdf_storage_path",
        "provider",
        "raw",
        "raw_error",
        "raw_ocr",
        "raw_text",
        "request_body",
        "response_body",
        "secret",
        "source_pdf_id",
        "source_page_indices",
        "storage_path",
        "system_prompt",
        "tenant_id",
        "typhoon_enhanced",
        "typhoon_pages",
        "user_id",
        "workspace_client_id",
        "input_tokens",
        "output_tokens",
    }
)

_BLOCKED_KEY_PARTS = (
    "api_key",
    "debug",
    "gemini",
    "model",
    "prompt",
    "provider",
    "secret",
    "storage_path",
    "token",
    "traceback",
)


def _blocked_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    name = key.lower()
    return (
        name.startswith("_") or name in _BLOCKED_KEYS or any(p in name for p in _BLOCKED_KEY_PARTS)
    )


def strip_internal_fields(obj: Any) -> Any:
    """递归剥离:① 所有 _ 前缀 key(每页内部 debug 留底)② 引擎/品牌标识 key。
    返回净化后的新结构,不改原对象(DB 留底已在上游落库)。"""
    if isinstance(obj, dict):
        return {k: strip_internal_fields(v) for k, v in obj.items() if not _blocked_key(k)}
    if isinstance(obj, list):
        return [strip_internal_fields(x) for x in obj]
    return obj
