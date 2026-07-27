# -*- coding: utf-8 -*-
"""web 进程内后台工人的起停壳(OCR / 对账 / 管家三处共用一份)。

三个 worker 此前各写过一份 start_embedded + stop_embedded:幂等判断、急停闸的读法、
等停 5 秒再 cancel 的收尾,三份逐字节相同。收成一份的理由不是省行数,是「停机等多久」
「急停闸怎么读」这两件事该只有一个答案 —— 分散三份时改了其中一处,另外两个 worker 不会
跟着动,而进程收尾的差异恰恰是部署现场最难复现的那一类。

急停语义不在这里定死:环境变量值 != "1" 就不起,但默认值由各 worker 自己给(OCR 走灰度
默认关,对账与管家默认开)—— 那是产品决定,不该被这层壳替它们做主。
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Awaitable, Callable, Optional

# 等停上限。超时说明主循环卡在某个不响应 stop_event 的调用里,只能硬 cancel —— 但先给它
# 一个自己收尾的机会,免得把正在写的一笔活拦腰截断。
STOP_TIMEOUT_S = 5


class EmbeddedWorker:
    """一个后台工人在 web 进程内的生命周期(起 / 停 / 幂等)。"""

    def __init__(
        self,
        tag: str,
        run: Callable[[asyncio.Event], Awaitable[None]],
        env_key: str,
        logger: logging.Logger,
        *,
        default: str = "1",
    ) -> None:
        self._tag = tag
        self._run = run
        self._env_key = env_key
        self._logger = logger
        self._default = default
        self._task: Optional[asyncio.Task] = None
        self._stop: Optional[asyncio.Event] = None

    @property
    def task(self) -> Optional[asyncio.Task]:
        """在跑的任务(没起 / 已收 = None)。只读:起停一律走 start / stop。"""
        return self._task

    def start(self) -> None:
        """在当前事件循环起后台工人任务。幂等 —— 重复调用不会起第二个。"""
        if self._task and not self._task.done():
            return
        if os.environ.get(self._env_key, self._default) != "1":
            self._logger.info(f"[{self._tag}] {self._env_key}!=1 · embedded worker not started")
            return
        self._stop = asyncio.Event()
        self._task = asyncio.create_task(self._run(self._stop))
        self._logger.info(f"[{self._tag}] embedded worker started")

    async def stop(self) -> None:
        if self._stop:
            self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=STOP_TIMEOUT_S)
            except Exception:  # noqa: BLE001
                self._task.cancel()
