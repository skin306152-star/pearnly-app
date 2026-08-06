# -*- coding: utf-8 -*-
"""管家路由契约 + fail-closed 守门(routes/steward_routes.py · B3 异步 + F1 万能口)。

锁:①十端点按 path+method 注册且挂进 app(前端 static/ai/ai-api-steward.js 逐条对齐);
②闸关(pearnly_ai_steward 或 m1 任一关)时业务端点一律 404、status 仍回 200
{enabled:false, attachments:{...}}(探针不制造 console 噪音,顺带把上传限额带给前端);
③别人的会话 404(会话是私人工作记录)。
"""

from __future__ import annotations

import unittest
from contextlib import ExitStack
from unittest import mock

from fastapi import HTTPException

from routes import steward_common as sc
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
        # 业务端点的门收口在 routes/steward_common(S1),status 探针仍在本模块拿
        # authorize_pearnly_ai —— 两处都桩,单一用例才能同时覆盖两条路径。
        return (
            mock.patch.object(sr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
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
        p1, p2, p3 = self._patches()
        with p1, p2, p3:
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
        p1, p2, p3 = self._patches()
        with p1, p2, p3:
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
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True
            ),
            mock.patch.object(sr.store, "ensure_once"),
            mock.patch.object(sc.store, "get_session", return_value=None) as get_session,
            mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await sr.get_session("s-other", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(get_session.call_args.kwargs["user_id"], "u1")


class SessionPageAttachmentScopeTests(unittest.IsolatedAsyncioTestCase):
    """分页端点把附件查询收窄到本页消息(附件随消息分页收窄,S1 三连读收敛同批)。"""

    def _patches(self, page, has_more=False):
        return (
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sc.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True
            ),
            mock.patch.object(sr.store, "ensure_once"),
            mock.patch.object(sr.store, "latest_task_id", return_value=None),
            mock.patch.object(sc.store, "get_session", return_value={"id": "s-1"}),
            mock.patch.object(sr.sessions_dal, "list_messages_page", return_value=(page, has_more)),
            mock.patch.object(sr.attachments, "list_for_message", return_value=[]),
            mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
        )

    async def test_page_request_scopes_attachment_query_to_page_ids(self):
        """分页请求下附件查询带本页消息 id 过滤:传 message_ids=[11,12],不是全会话。"""
        page = [
            {"id": 11, "role": "user", "text": "hi"},
            {"id": 12, "role": "assistant", "text": "yo"},
        ]
        with ExitStack() as stack:
            _, _, _, _, _, _, lfm, _ = (stack.enter_context(p) for p in self._patches(page))
            out = await sr.get_session("s-1", mock.Mock())
        self.assertEqual([m["id"] for m in out["messages"]], ["11", "12"])
        lfm.assert_called_once_with(
            mock.ANY, tenant_id="t-1", session_id="s-1", message_ids=[11, 12]
        )

    async def test_empty_page_skips_attachment_query(self):
        """页内无消息时跳过附件查询(不存在传空 list 再查一次的浪费)。"""
        with ExitStack() as stack:
            _, _, _, _, _, _, lfm, _ = (stack.enter_context(p) for p in self._patches([], True))
            out = await sr.get_session("s-1", mock.Mock())
        self.assertEqual(out["messages"], [])
        self.assertTrue(out["has_more"])
        lfm.assert_not_called()


class AttachmentDalScopeTests(unittest.TestCase):
    def test_message_ids_produces_message_id_filter_in_sql(self):
        """DAL 层:传 message_ids 时 SQL 带 AND message_id = ANY(%s),页外消息不白查。"""
        from services.steward import attachments

        class _CaptureCur(FakeCur):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                self.sql = ""
                self.args = None

            def execute(self, sql, args=None):
                self.sql = sql
                self.args = args

        cur = _CaptureCur(rows=[])
        rows = attachments.list_for_message(
            cur, tenant_id="t-1", session_id="s-1", message_ids=[11, 12]
        )
        self.assertEqual(rows, [])
        self.assertIn("AND message_id = ANY(%s)", cur.sql)
        self.assertEqual(cur.args[-1], ["11", "12"])


if __name__ == "__main__":
    unittest.main()
