# -*- coding: utf-8 -*-
"""人话渲染 + error_code→i18n key 映射(WP1 持有 · 键名锁定 docs/agent/CONVERSATION-SPEC.md)。

所有用户可见文本只在这一处产出 —— executor 的回执、loop 的反问/超范围/失败说明都过这里。
键名是 WP1↔WP3 对齐的唯一源(抄 spec 表,不互改对方文件):失败一律 agent.failure.*、成功回执
agent.ok.*。M1 返回「key(+slots)」占位串,WP3 在 i18n-data.js 落 4 语;WP5 接 i18n 渲染时
copy_map 内部换成真渲染,调用点(executor/loop)不变。
"""

from __future__ import annotations

from services.agent.contracts import ToolSpec

# 失败码 → i18n key(CONVERSATION-SPEC §1.5 · 前缀 agent.failure.*)。
ERROR_COPY: dict[str, str] = {
    "insufficient_balance": "agent.failure.insufficient_balance",
    "no_endpoint": "agent.failure.no_endpoint",
    "forbidden": "agent.failure.forbidden",
    "history_not_found": "agent.failure.history_not_found",
    "no_tenant": "agent.failure.no_tenant",
    "query_failed": "agent.failure.query_failed",
    "not_available_yet": "agent.failure.not_available_yet",
    "not_implemented_m1": "agent.failure.not_available_yet",  # B 档留桩 → spec 的 not_available_yet
    "unknown": "agent.failure.unknown",
}
_FAILURE_DEFAULT = "agent.failure._default"

# 成功回执 → i18n key(§1.3 · 每个 M1 工具一个 agent.ok.*)。
OK_COPY: dict[str, str] = {
    "list_history": "agent.ok.history",
    "history_summary": "agent.ok.history_summary",
    "balance": "agent.ok.balance",
    "usage_this_month": "agent.ok.usage_this_month",
    "list_notifications": "agent.ok.notifications",
}

# 反问 slot → i18n key(§1.1)。未登记的 slot → 通用「哪一张」。
ASK_COPY: dict[str, str] = {
    "keyword": "agent.ask.which_doc",
    "status": "agent.ask.which_doc",
    "period": "agent.ask.period",
    "endpoint_id": "agent.ask.endpoint",
    "amount": "agent.ask.amount",
}
_ASK_DEFAULT = "agent.ask.which_doc"

_OOS_DEFAULT = "agent.oos.capability"  # §1.4 超范围必带「我能做什么」出口
_CHAT_DEFAULT = "agent.chat.greeting"  # §1.6 沿用现有语气池


def _render(key: str, **slots) -> str:
    """key(+slots)占位串。WP5 接 i18n 时换成真渲染,调用点不变。"""
    if not slots:
        return key
    payload = ";".join(f"{k}={v}" for k, v in slots.items())
    return f"{key}|{payload}"


# ── loop 用 ──────────────────────────────────────────────────────────────


def out_of_scope(message: str = "") -> str:
    return _OOS_DEFAULT


def chat(message: str = "") -> str:
    return _CHAT_DEFAULT


def ask(field: str) -> str:
    return ASK_COPY.get(field, _ASK_DEFAULT)


def confirm(spec: ToolSpec, grounded: dict) -> str:
    """B 档执行前复述确认(§1.2 · M3 才有 B 档工具走到这里)。"""
    return f"agent.confirm.{spec.name}"


def failure(error_code: str | None) -> str:
    return ERROR_COPY.get(error_code or "unknown", _FAILURE_DEFAULT)


# ── executor 回执(§1.3) ─────────────────────────────────────────────────


def history_receipt(items: list, total: int) -> str:
    return _render(OK_COPY["list_history"], count=total, shown=len(items))


def history_summary_receipt(counts: dict) -> str:
    slots = {k: counts[k] for k in sorted(counts or {})}
    return _render(OK_COPY["history_summary"], **slots)


def balance_receipt(billing: dict) -> str:
    b = billing or {}
    return _render(
        OK_COPY["balance"],
        balance=f"{float(b.get('balance_thb') or 0):.2f}",
        pages=int(b.get("pages_used_this_month") or 0),
    )


def usage_receipt(billing: dict) -> str:
    return _render(
        OK_COPY["usage_this_month"], pages=int((billing or {}).get("pages_used_this_month") or 0)
    )


def notifications_receipt(logs: list) -> str:
    return _render(OK_COPY["list_notifications"], count=len(logs or []))


__all__ = [
    "ERROR_COPY",
    "OK_COPY",
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
