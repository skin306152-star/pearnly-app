# -*- coding: utf-8 -*-
"""services/observability · REFACTOR-WA-B6 · 结构化日志 + 全链路上下文。

- log_context:请求级 contextvar(request_id / user_id / tenant_id)+ 日志 Filter
- logging_config:configure_logging() 统一日志格式(JSON / text)
- request_context:纯 ASGI 中间件 · 每请求绑定 request_id 并回写响应头
"""
