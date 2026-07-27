# -*- coding: utf-8 -*-
"""web 进程内后台工人起停壳(services/embedded_worker.py)。

锁四件:①急停闸 != "1" 就不起(默认值由各 worker 自己给,壳不替它们决定);②起两次只有
一个任务在跑(app 重入启动事件时不会起第二个工人抢同一批活);③stop 先给主循环自己收尾
的机会,卡死才 cancel;④OCR / 对账 / 管家三处真共用这一份 —— 这条是收口的反证,防哪天
又各自复制回去。
"""

from __future__ import annotations

import asyncio
import logging
import os
import unittest
from unittest import mock

from services.embedded_worker import STOP_TIMEOUT_S, EmbeddedWorker

_LOG = logging.getLogger("test.embedded_worker")


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _fast_stop():
    """把等停上限压到毫秒级。单测不该真等 5 秒去验一条超时分支。"""
    return mock.patch("services.embedded_worker.STOP_TIMEOUT_S", 0.01)


class StartGateTests(unittest.TestCase):
    def test_flag_off_starts_nothing(self):
        async def scenario():
            w = EmbeddedWorker("t", _never, "T_ASYNC", _LOG)
            with mock.patch.dict(os.environ, {"T_ASYNC": "0"}, clear=False):
                w.start()
            self.assertIsNone(w.task)

        _run(scenario())

    def test_flag_absent_falls_back_to_the_workers_own_default(self):
        """默认值是各 worker 的产品决定(OCR 灰度默认关,对账/管家默认开),壳只照做。"""

        async def scenario():
            env = {k: v for k, v in os.environ.items() if k != "T_ASYNC"}
            with mock.patch.dict(os.environ, env, clear=True):
                off = EmbeddedWorker("t", _never, "T_ASYNC", _LOG, default="0")
                off.start()
                self.assertIsNone(off.task)

                on = EmbeddedWorker("t", _never, "T_ASYNC", _LOG)
                on.start()
                self.assertIsNotNone(on.task)
                with _fast_stop():
                    await on.stop()

        _run(scenario())


class IdempotenceTests(unittest.TestCase):
    def test_second_start_does_not_spawn_a_second_worker(self):
        async def scenario():
            w = EmbeddedWorker("t", _never, "T_ASYNC", _LOG)
            with mock.patch.dict(os.environ, {"T_ASYNC": "1"}, clear=False):
                w.start()
                first = w.task
                w.start()
            self.assertIs(w.task, first)
            with _fast_stop():
                await w.stop()

        _run(scenario())


class StopTests(unittest.TestCase):
    def test_stop_lets_the_loop_finish_its_own_work(self):
        """正常收尾走 stop_event,不 cancel —— 半路截断会把正在写的一笔活留成半截。"""
        seen = {}

        async def loop(stop):
            await stop.wait()
            seen["clean"] = True

        async def scenario():
            w = EmbeddedWorker("t", loop, "T_ASYNC", _LOG)
            with mock.patch.dict(os.environ, {"T_ASYNC": "1"}, clear=False):
                w.start()
            await w.stop()
            self.assertTrue(seen.get("clean"))
            self.assertFalse(w.task.cancelled())

        _run(scenario())

    def test_a_loop_that_ignores_stop_gets_cancelled(self):
        async def scenario():
            w = EmbeddedWorker("t", _never, "T_ASYNC", _LOG)
            with mock.patch.dict(os.environ, {"T_ASYNC": "1"}, clear=False):
                w.start()
            with _fast_stop():
                await w.stop()  # _never 不看 stop_event · 只能等超时后硬 cancel
            with self.assertRaises(asyncio.CancelledError):
                await w.task

        _run(scenario())

    def test_stop_timeout_is_generous_enough_to_be_a_grace_period(self):
        self.assertGreaterEqual(STOP_TIMEOUT_S, 1)


class SingleShellTests(unittest.TestCase):
    def test_all_three_workers_use_this_shell(self):
        """反证:收口报绿得是因为三处真共用一份,不是因为它们各自又复制了一份回去。"""
        from services.ocr.jobs import worker as ocr
        from services.recon_jobs import worker as recon
        from services.steward import worker as steward

        for mod in (ocr, recon, steward):
            self.assertIsInstance(mod._embedded, EmbeddedWorker, mod.__name__)
            # 起停一律走壳:模块里不该再留 global 的 task/stop 状态。
            self.assertFalse(hasattr(mod, "_embedded_task"), mod.__name__)


async def _never(stop: asyncio.Event) -> None:
    """永不自行退出的假主循环(测起停用,不测循环体)。"""
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    unittest.main()
