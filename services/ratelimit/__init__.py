# -*- coding: utf-8 -*-
"""services/ratelimit · REFACTOR-WA-B5 · API 全局限流。

- limiter:进程内固定窗口计数器(无外部依赖 / 无 Redis)
- middleware:纯 ASGI 限流中间件 · 保守限额 · 豁免基建 · fail-open
"""
