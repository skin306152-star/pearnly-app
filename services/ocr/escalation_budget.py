# -*- coding: utf-8 -*-
"""贵模型回落(escalate/fallback)的跑批级配额(R1 · 件三)。

问题:economy 档下低置信页会升高精档重读(约贵 3×);单次全量跑批若大量升级
= 成本失控(真跑 15 张打 45 次调用的病根之一)。本模块给「一次跑批最多回落几次」一个
上限:用尽后该页不再升级,走既有诚实路径(needs_review 交人审),模型选择/路由表/判读
逻辑/prompt 一字不改——这里只管「这次要不要花那笔升级钱」的布尔闸。

契约:未设预算(contextvar 为空)= 无限(单张 OCR/主站散单等非跑批路径行为逐字节不变)。
设了预算 = 每次放行扣一次额度,扣光即拒。预算对象线程安全:多页 PDF 在 page_runner 里
fan-out 到子线程(copy_context 传播同一个 mutable 预算对象),并发页共享同一计数,全局递减。
跨「件」的 ThreadPool 不 copy_context,故调用方(classify._ocr_safe)在每个 worker 内显式
set_budget 指向同一预算对象(与 attribution 同款 per-worker 播种)。
"""

from __future__ import annotations

import threading
from contextvars import ContextVar, Token
from typing import Optional

_BUDGET: ContextVar[Optional["Budget"]] = ContextVar("ocr_escalation_budget", default=None)


class Budget:
    """回落额度计数(线程安全)。跑批一批 OCR 共用一个实例,跨并发页/件全局递减。"""

    def __init__(self, limit: int):
        self._remaining = int(limit)
        self._lock = threading.Lock()

    def try_consume(self) -> bool:
        with self._lock:
            if self._remaining <= 0:
                return False
            self._remaining -= 1
            return True

    @property
    def remaining(self) -> int:
        with self._lock:
            return self._remaining


def new_budget(limit: int) -> Budget:
    return Budget(limit)


def set_budget(budget: Optional[Budget]) -> Token:
    """把预算绑到当前上下文(worker 内调,finally 里 reset_budget)。"""
    return _BUDGET.set(budget)


def reset_budget(token: Token) -> None:
    _BUDGET.reset(token)


def try_escalate() -> bool:
    """本次回落是否放行:未设预算 = 无限(行为不变);设了则放行即扣一次额度,扣光即拒。"""
    budget = _BUDGET.get()
    return True if budget is None else budget.try_consume()
