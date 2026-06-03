# -*- coding: utf-8 -*-
"""services/observability/log_context.py · REFACTOR-WA-B6 · 全链路日志上下文。

contextvars 随 asyncio task 隔离 · 并发请求互不串味。每条日志由 ContextFilter
自动补上当前上下文字段(见 logging_config.JsonFormatter)。

    from services.observability import log_context
    tokens = log_context.bind(request_id="...", tenant_id="...")
    try:
        ...                       # 期间任意 logger 调用都会带上这些字段
    finally:
        log_context.reset(tokens)
"""

from __future__ import annotations

import contextvars
import logging
from typing import Dict, Optional

# 字段顺序固定 · JSON 输出与文本格式都按此引用
FIELDS = ("request_id", "user_id", "tenant_id")

_VARS: Dict[str, "contextvars.ContextVar[Optional[str]]"] = {
    name: contextvars.ContextVar(name, default=None) for name in FIELDS
}


def bind(
    *,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, object]:
    """绑定上下文 · 仅覆盖显式传入的非 None 值。返回 token 字典供 reset()。"""
    incoming = {"request_id": request_id, "user_id": user_id, "tenant_id": tenant_id}
    tokens: Dict[str, object] = {}
    for name, value in incoming.items():
        if value is not None:
            tokens[name] = _VARS[name].set(str(value))
    return tokens


def reset(tokens: Dict[str, object]) -> None:
    """还原 bind() 设置的字段 · 顺序无关(每个字段独立 token)。"""
    for name, token in tokens.items():
        _VARS[name].reset(token)  # type: ignore[arg-type]


def current() -> Dict[str, Optional[str]]:
    """当前上下文快照(未绑定字段为 None)。"""
    return {name: var.get() for name, var in _VARS.items()}


class ContextFilter(logging.Filter):
    """把当前上下文字段塞进每条 LogRecord(未绑定时填 '-')· 供 formatter 引用。"""

    def filter(self, record: logging.LogRecord) -> bool:
        for name, var in _VARS.items():
            setattr(record, name, var.get() or "-")
        return True
