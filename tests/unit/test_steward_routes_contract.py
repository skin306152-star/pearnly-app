# -*- coding: utf-8 -*-
"""管家路由契约 + fail-closed 守门(routes/steward_routes.py · B3 异步 + F1 万能口)。

锁:①十端点按 path+method 注册且挂进 app(前端 static/ai/ai-api-steward.js 逐条对齐);
②闸关(pearnly_ai_steward 或 m1 任一关)时业务端点一律 404、status 仍回 200
{enabled:false, attachments:{...}}(探针不制造 console 噪音,顺带把上传限额带给前端);
③别人的会话 404(会话是私人工作记录)。
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
    ("POST", "/api/ai/steward/sessions/{session_id}/attachments"),
    ("POST", "/api/ai/steward/sessions/{session_id}/messages"),
    ("GET", "/api/ai/steward/attachments/{attachment_id}/download"),
    ("GET", "/api/ai/steward/tasks/{task_id}"),
    ("POST", "/api/ai/steward/tasks/{task_id}/cancel"),
    ("POST", "/api/ai/steward/authorizations/approve"),
    ("POST", "/api/ai/steward/authorizations/reject"),
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
            await self._assert_404(sr.cancel_task("t-9", mock.Mock()))
            await self._assert_404(
                sr.post_message("s-1", sr.MessageIn(text="本期谁缺料"), mock.Mock())
            )
            await self._assert_404(sr.add_attachments("s-1", mock.Mock(), files=[]))
            await self._assert_404(sr.download_attachment("a-1", mock.Mock()))
            decision = sr.AuthzDecisionIn(token="tok-12345678")
            await self._assert_404(sr.approve_authorization(decision, mock.Mock()))
            await self._assert_404(sr.reject_authorization(decision, mock.Mock()))

    async def test_status_probe_reports_false_instead_of_404(self):
        p1, p2 = self._patches()
        with p1, p2:
            out = await sr.get_status(mock.Mock())
        self.assertFalse(out["enabled"])

    async def test_status_probe_reports_true_when_open(self):
        with (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True
            ),
        ):
            out = await sr.get_status(mock.Mock())
        self.assertTrue(out["enabled"])

    async def test_status_carries_upload_limits_so_frontend_never_hardcodes_them(self):
        """上限单一事实源:前端要在选文件当下就拒,但那份数字必须从这里读。"""
        from services.steward import attachments

        with (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True
            ),
        ):
            limits = (await sr.get_status(mock.Mock()))["attachments"]
        self.assertEqual(limits["max_file_bytes"], attachments.MAX_FILE_BYTES)
        self.assertEqual(limits["max_batch_bytes"], attachments.MAX_BATCH_BYTES)
        self.assertEqual(limits["max_files"], attachments.MAX_FILES_PER_MESSAGE)
        self.assertIn(".pdf", limits["accept"])


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
