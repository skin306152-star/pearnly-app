# -*- coding: utf-8 -*-
"""services/line_dms/_out.py · flow/booking 共享出口工具(后台 spawn + reply/push · dms channel)。"""

import asyncio
import unittest
from unittest import mock

from services.line_dms import _out


class ReplyPushTests(unittest.TestCase):
    def test_reply_skips_when_no_token(self):
        with mock.patch.object(_out.line_client, "reply_text") as reply:
            _out._reply("", "hi")
        reply.assert_not_called()

    def test_reply_sends_on_dms_channel(self):
        with mock.patch.object(_out.line_client, "reply_text") as reply:
            _out._reply("rt", "hi")
        reply.assert_called_once_with("rt", "hi", channel="dms")

    def test_push_sends_on_dms_channel(self):
        with mock.patch.object(_out.line_client, "push_text") as push:
            _out._push("L1", "hi")
        push.assert_called_once_with("L1", "hi", channel="dms")


class SpawnTests(unittest.IsolatedAsyncioTestCase):
    async def test_spawn_runs_coro_on_running_loop(self):
        ran = []

        async def work():
            ran.append(True)

        _out.make_spawn("test.tag")(work())
        await asyncio.sleep(0)  # 让被调度的后台 task 跑一轮
        self.assertEqual(ran, [True])


class SpawnNoLoopTests(unittest.TestCase):
    def test_spawn_without_loop_drops_without_raising(self):
        async def work():
            return None

        coro = work()
        _out.make_spawn("test.tag")(coro)  # 无 running loop → 只告警丢弃,不抛
        coro.close()  # 显式关闭,避免 "never awaited" 警告


if __name__ == "__main__":
    unittest.main()
