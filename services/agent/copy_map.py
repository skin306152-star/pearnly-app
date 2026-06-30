# -*- coding: utf-8 -*-
"""人话渲染 + error_code→i18n key 映射(WP1 建结构 · WP3 填真值)。

所有用户可见文本只在这一处产出 —— executor 的回执、loop 的反问/超范围/失败说明都过这里。
M1 先给确定性占位串(键名 + 关键数字),WP3 把内部换成 4 语 i18n;调用点(executor/loop)不变。
"""

from __future__ import annotations

from services.agent.contracts import ToolSpec

# 机器错误码 → i18n key(WP3 在 static/i18n-data.js 落 4 语文案)。
ERROR_COPY: dict[str, str] = {
    "history_not_found": "agent.err.history_not_found",
    "no_endpoint": "agent.err.no_endpoint",
    "no_tenant": "agent.err.no_tenant",
    "forbidden": "agent.err.forbidden",
    "skipped_dup": "agent.err.skipped_dup",
    "not_implemented_m1": "agent.err.not_available_yet",
    "query_failed": "agent.err.query_failed",
    "unknown": "agent.err.unknown",
}

# 反问时 slot → 提示 i18n key(WP3 落文案)。未登记 → 通用追问。
ASK_COPY: dict[str, str] = {
    "keyword": "agent.ask.keyword",
    "status": "agent.ask.status",
}


def _key(prefix: str, code: str) -> str:
    return f"[{prefix}:{code}]"


# ── loop 用 ──────────────────────────────────────────────────────────────


def out_of_scope(message: str = "") -> str:
    """超范围 → 引导回能做的事。"""
    return _key("out_of_scope", "default")


def chat(message: str = "") -> str:
    """闲聊/问候。"""
    return _key("chat", "default")


def ask(field: str) -> str:
    """缺参数 → 反问。"""
    return _key("ask", ASK_COPY.get(field, field or "missing"))


def confirm(spec: ToolSpec, grounded: dict) -> str:
    """B 档执行前复述确认(M3 才有 B 档工具走到这里)。"""
    return _key("confirm", spec.name)


def failure(error_code: str | None) -> str:
    """工具失败 → 人话说明。"""
    return _key("failure", ERROR_COPY.get(error_code or "unknown", "agent.err.unknown"))


# ── executor 回执 ────────────────────────────────────────────────────────


def history_receipt(items: list, total: int) -> str:
    return _key("receipt.history", f"shown={len(items)};total={total}")


def history_summary_receipt(counts: dict) -> str:
    parts = ";".join(f"{k}={v}" for k, v in sorted((counts or {}).items()))
    return _key("receipt.history_summary", parts)


def balance_receipt(billing: dict) -> str:
    return _key("receipt.balance", f"thb={float((billing or {}).get('balance_thb') or 0):.2f}")


def usage_receipt(billing: dict) -> str:
    return _key("receipt.usage", f"pages={int((billing or {}).get('pages_used_this_month') or 0)}")


def notifications_receipt(logs: list) -> str:
    return _key("receipt.notifications", f"count={len(logs or [])}")


__all__ = [
    "ERROR_COPY",
    "ASK_COPY",
    "out_of_scope",
    "chat",
    "ask",
    "confirm",
    "failure",
    "history_receipt",
    "history_summary_receipt",
    "balance_receipt",
    "usage_receipt",
    "notifications_receipt",
]
