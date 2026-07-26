# -*- coding: utf-8 -*-
"""管家路由契约 + fail-closed 守门(routes/steward_routes.py · B2-M1)。

锁:①五端点按 path+method 注册且挂进 app(前端 static/ai/ai-api-steward.js 逐条对齐);
②闸关(pearnly_ai_steward 或 m1 任一关)时四个业务端点一律 404、status 仍回 200
{enabled:false}(探针不制造 console 噪音);③别人的会话 404(会话是私人工作记录)。
"""

from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from routes import steward_routes as sr
from tests.unit._route_contract_fakes import CurCM, FakeCur, route_set as _route_set

_USER = {"id": "u1", "tenant_id": "t-1"}
_EXPECTED = {
    ("GET", "/api/ai/steward/status"),
    ("POST", "/api/ai/steward/sessions"),
    ("GET", "/api/ai/steward/sessions/{session_id}"),
    ("POST", "/api/ai/steward/sessions/{session_id}/messages"),
    ("GET", "/api/ai/steward/tasks/{task_id}"),
}


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        self.assertEqual(_route_set(sr.router), _EXPECTED)

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        for _method, path in _EXPECTED:
            self.assertIn(path, paths)


class GateClosedTests(unittest.IsolatedAsyncioTestCase):
    def _patches(self):
        return (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=False
            ),
        )

    async def _assert_404(self, coro):
        with self.assertRaises(HTTPException) as ctx:
            await coro
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "steward.not_found")

    async def test_business_endpoints_404_when_gate_closed(self):
        p1, p2 = self._patches()
        with p1, p2:
            await self._assert_404(sr.create_session(mock.Mock()))
            await self._assert_404(sr.get_session("s-1", mock.Mock()))
            await self._assert_404(sr.get_task("t-9", mock.Mock()))
            await self._assert_404(
                sr.post_message("s-1", sr.MessageIn(text="本期谁缺料"), mock.Mock())
            )

    async def test_status_probe_reports_false_instead_of_404(self):
        p1, p2 = self._patches()
        with p1, p2:
            self.assertEqual(await sr.get_status(mock.Mock()), {"enabled": False})

    async def test_status_probe_reports_true_when_open(self):
        with (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True
            ),
        ):
            self.assertEqual(await sr.get_status(mock.Mock()), {"enabled": True})


class SessionOwnershipTests(unittest.IsolatedAsyncioTestCase):
    async def test_other_persons_session_is_404(self):
        with (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True
            ),
            mock.patch.object(sr.store, "ensure_once"),
            mock.patch.object(sr.store, "get_session", return_value=None) as get_session,
            mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await sr.get_session("s-other", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(get_session.call_args.kwargs["user_id"], "u1")


if __name__ == "__main__":
    unittest.main()
