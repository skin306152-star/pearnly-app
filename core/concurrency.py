# -*- coding: utf-8 -*-
"""线程池提交的上下文快照助手。

请求级状态全在 contextvars(成本归因 usage_context / 引擎档 engine_policy /
网关归因 attribution):裸 executor.submit 起的子线程读不到,落账进「未归因」。
收单点后新增并发点没有第二种写法可选。
"""

from __future__ import annotations

import contextvars


def submit_ctx(executor, fn, /, *args, **kwargs):
    """executor.submit + 提交时刻的 contextvars 快照。子线程继承请求上下文。"""
    return executor.submit(contextvars.copy_context().run, fn, *args, **kwargs)
