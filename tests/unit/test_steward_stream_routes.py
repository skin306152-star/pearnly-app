# -*- coding: utf-8 -*-
"""管家任务事件 SSE 契约(routes/steward_stream_routes.py · S1)。

锁:①端点注册且挂进 app;②闸关/任务不存在 404(与 GET /tasks/{tid} 同口径);
③流:首帧带投影、投影没变不重发、终态帧后跟 end(terminal) 收口;④连接到时发
end(timeout)(任务还在跑,前端回落轮询);⑤DB 读走 asyncio.to_thread,事件循环
上不跑同步游标(常驻流挂住循环 = 同进程所有请求一起卡)。
"""

from __future__ import annotations

import asyncio
import json
import unittest
from contextlib import ExitStack
from unittest import mock

from fastapi import HTTPException

from routes import steward_common as sc
from routes import steward_stream_routes as str_r
from tests.unit._route_contract_fakes import route_set as _route_set

_USER = {"id": "u1", "tenant_id": "t-1"}


def _drain(gen, n=50):
    async def run():
        out = []
        for _ in range(n):
            try:
                out.append(await asyncio.wait_for(gen.__anext__(), timeout=2))
            except StopAsyncIteration:
                break
        return out

    return asyncio.run(run())


def _events(frames):
    out = []
    for f in frames:
        if f.startswith("event:"):
            head, _, data = f.partition("\ndata: ")
            out.append((head.split("event: ")[1].strip(), json.loads(data.strip())))
    return out


class RouteContractTests(unittest.TestCase):
    def test_route_registered(self):
        self.assertEqual(
            _route_set(str_r.router), {("GET", "/api/ai/steward/tasks/{task_id}/events")}
        )

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        self.assertIn("/api/ai/steward/tasks/{task_id}/events", paths)


class GateTests(unittest.IsolatedAsyncioTestCase):
    async def test_gate_closed_is_404(self):
        with (
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sc.feature_flags, "pearnly_ai_steward_enabled_for", return_value=False
            ),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await str_r.task_events("t-1", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_unknown_task_is_404_before_stream_starts(self):
        with (
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sc.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True
            ),
            mock.patch.object(str_r.store, "ensure_once"),
            mock.patch.object(str_r, "_read_task", return_value=None),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await str_r.task_events("t-ghost", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)


class StreamTests(unittest.TestCase):
    def _run(self, snapshots, max_ticks=10):
        """snapshots 按 tick 顺序喂 _read_task;不足时重复末一帧。"""
        seq = list(snapshots)

        def read(_tenant, _task, _heal):
            return seq.pop(0) if len(seq) > 1 else seq[0]

        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(str_r, "_read_task", side_effect=read))
            stack.enter_context(mock.patch.object(str_r, "_MAX_TICKS", max_ticks))
            stack.enter_context(mock.patch.object(str_r, "_TICK_S", 0))
            return _events(_drain(str_r._event_stream("t-1", "task-1")))

    def test_terminal_task_emits_one_frame_then_end(self):
        done = {"task_id": "task-1", "status": "done", "steps": []}
        events = self._run([done])
        self.assertEqual(events[0], ("task", done))
        self.assertEqual(events[1], ("end", {"reason": "terminal"}))
        self.assertEqual(len(events), 2)

    def test_unchanged_snapshot_is_not_re_emitted(self):
        running = {"task_id": "task-1", "status": "running", "steps": [{"id": "s1"}]}
        done = dict(running, status="done")
        events = self._run([running, running, running, done])
        kinds = [e[0] for e in events]
        # running 一帧 + done 一帧 + end,中间没变的拍不重发。
        self.assertEqual(kinds, ["task", "task", "end"])
        self.assertEqual(events[1][1]["status"], "done")

    def test_waiting_user_counts_as_terminal_for_the_stream(self):
        # 等人批卡 = 流收口(批完由决断响应重启盯梢,同轮询的 isTerminal 口径)。
        waiting = {"task_id": "task-1", "status": "waiting_user", "steps": []}
        events = self._run([waiting])
        self.assertEqual(events[-1], ("end", {"reason": "terminal"}))

    def test_connection_cap_reports_timeout(self):
        running = {"task_id": "task-1", "status": "running", "steps": []}
        events = self._run([running], max_ticks=3)
        self.assertEqual(events[-1], ("end", {"reason": "timeout"}))

    def test_vanished_task_ends_stream(self):
        events = self._run([None])
        self.assertEqual(events, [("end", {"reason": "terminal"})])


class ThreadOffloadTests(unittest.TestCase):
    def test_db_read_never_runs_on_the_event_loop(self):
        """tripwire:_read_task 若在事件循环线程里被调,当场炸(verification skill §4)。"""
        running = {"task_id": "task-1", "status": "done", "steps": []}

        def read(_tenant, _task, _heal):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return running
            raise AssertionError("sync DB read ran on the event loop")

        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(str_r, "_read_task", side_effect=read))
            stack.enter_context(mock.patch.object(str_r, "_TICK_S", 0))
            events = _events(_drain(str_r._event_stream("t-1", "task-1")))
        self.assertEqual(events[-1][0], "end")


if __name__ == "__main__":
    unittest.main()
