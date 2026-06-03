# -*- coding: utf-8 -*-
"""services/observability/logging_config.py · REFACTOR-WA-B6 · 结构化日志配置。

configure_logging() 替代 app.py 裸 logging.basicConfig:
  - LOG_FORMAT=json(默认 · 生产 journald 单行 JSON · 可 grep/聚合)
  - LOG_FORMAT=text(本地开发人读)
两种格式都挂 ContextFilter · request_id / user_id / tenant_id 字段一致。
"""

from __future__ import annotations

import json
import logging
import os

from services.observability.log_context import FIELDS, ContextFilter


class JsonFormatter(logging.Formatter):
    """每条日志输出一行 JSON · 含上下文字段与(可选)异常栈。"""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for field in FIELDS:
            payload[field] = getattr(record, field, "-")
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _build_formatter(fmt: str) -> logging.Formatter:
    if fmt == "json":
        return JsonFormatter()
    return logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s "
        "[req=%(request_id)s tid=%(tenant_id)s uid=%(user_id)s]: %(message)s"
    )


def configure_logging() -> None:
    """配置 root logger:单 StreamHandler + ContextFilter + 选定格式。

    清空既有 handler 防与 basicConfig 双写;幂等(重复调用只保留一个 handler)。
    """
    level = os.environ.get("LOG_LEVEL", "INFO")
    fmt = (os.environ.get("LOG_FORMAT") or "json").strip().lower()

    handler = logging.StreamHandler()
    handler.setFormatter(_build_formatter(fmt))
    handler.addFilter(ContextFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
