# -*- coding: utf-8 -*-
"""管家会话管理路由契约(routes/steward_session_routes.py · S1)。

锁:①五端点按 path+method 注册且挂进 app;②闸关一律 404(fail-closed,与主组同码);
③改名纯空白 422、找不到 404;④删除先删行后删盘上原件;⑤已送出的附件 409 拒删
(对话留痕不许改历史);⑥余额端点先判会话归属再出数字。
"""

from __future__ import annotations

import unittest
from contextlib import ExitStack
from unittest import mock

from fastapi import HTTPException

from routes import steward_common as sc
from routes import steward_session_routes as ssr
from tests.unit._route_contract_fakes import CurCM, FakeCur, route_set as _route_set

_USER = {"id": "u1", "tenant_id": "t-1"}
_SESSION = {"id": "s-1", "tenant_id": "t-1", "user_id": "u1"}
_EXPECTED = {
    ("GET", "/api/ai/steward/sessions"),
    ("POST", "/api/ai/steward/sessions/{session_id}/rename"),
    ("POST", "/api/ai/steward/sessions/{session_id}/delete"),
    ("POST", "/api/ai/steward/attachments/{attachment_id}/delete"),
    ("GET", "/api/ai/steward/budget"),
}


def _open_gate(stack: ExitStack, cur=None) -> None:
    for patch in (
        mock.patch.object(sc, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
        mock.patch.object(sc.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True),
        mock.patch.object(ssr.store, "ensure_once"),
        mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(cur or FakeCur())),
    ):
        stack.enter_context(patch)


class RouteContractTests(unittest.TestCase):
    def test_expected_routes_registered(self):
        self.assertEqual(_route_set(ssr.router), _EXPECTED)

    def test_mounted_in_app(self):
        import app  # noqa: F401

        paths = {getattr(r, "path", None) for r in app.app.routes}
        for _method, path in _EXPECTED:
            self.assertIn(path, paths)


class GateClosedTests(unittest.IsolatedAsyncioTestCase):
    async def _assert_404(self, coro):
        with self.assertRaises(HTTPException) as ctx:
            await coro
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "steward.not_found")

    async def test_all_endpoints_404_when_gate_closed(self):
        with (
            mock.patch.object(sc, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
            mock.patch.object(
                sc.feature_flags, "pearnly_ai_steward_enabled_for", return_value=False
            ),
        ):
            await self._assert_404(ssr.list_sessions(mock.Mock()))
            await self._assert_404(
                ssr.rename_session("s-1", ssr.RenameIn(title="改名"), mock.Mock())
            )
            await self._assert_404(ssr.delete_session("s-1", mock.Mock()))
            await self._assert_404(ssr.delete_attachment("a-1", mock.Mock()))
            await self._assert_404(ssr.get_budget(mock.Mock(), session_id="s-1"))


class RenameTests(unittest.IsolatedAsyncioTestCase):
    async def test_blank_title_is_422(self):
        with ExitStack() as stack:
            _open_gate(stack)
            with self.assertRaises(HTTPException) as ctx:
                await ssr.rename_session("s-1", ssr.RenameIn(title="   "), mock.Mock())
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "steward.empty_title")

    async def test_missing_session_is_404(self):
        with ExitStack() as stack:
            _open_gate(stack)
            stack.enter_context(
                mock.patch.object(ssr.sessions_dal, "rename_session", return_value=False)
            )
            with self.assertRaises(HTTPException) as ctx:
                await ssr.rename_session("s-x", ssr.RenameIn(title="改名"), mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_rename_echoes_trimmed_title(self):
        with ExitStack() as stack:
            _open_gate(stack)
            dal = stack.enter_context(
                mock.patch.object(ssr.sessions_dal, "rename_session", return_value=True)
            )
            out = await ssr.rename_session("s-1", ssr.RenameIn(title="  6 月对账  "), mock.Mock())
        self.assertEqual(out, {"ok": True, "title": "6 月对账"})
        self.assertEqual(dal.call_args.kwargs["title"], "6 月对账")


class DeleteSessionTests(unittest.IsolatedAsyncioTestCase):
    async def test_files_removed_after_row_delete(self):
        with ExitStack() as stack:
            _open_gate(stack)
            stack.enter_context(
                mock.patch.object(
                    ssr.sessions_dal, "delete_session", return_value=["/x/1.bin", "/x/2.bin"]
                )
            )
            removed = stack.enter_context(mock.patch.object(ssr.attachments, "remove_file"))
            out = await ssr.delete_session("s-1", mock.Mock())
        self.assertEqual(out, {"ok": True})
        self.assertEqual([c.args[0] for c in removed.call_args_list], ["/x/1.bin", "/x/2.bin"])

    async def test_missing_session_is_404_and_removes_nothing(self):
        with ExitStack() as stack:
            _open_gate(stack)
            stack.enter_context(
                mock.patch.object(ssr.sessions_dal, "delete_session", return_value=None)
            )
            removed = stack.enter_context(mock.patch.object(ssr.attachments, "remove_file"))
            with self.assertRaises(HTTPException) as ctx:
                await ssr.delete_session("s-x", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)
        removed.assert_not_called()


class DeleteAttachmentTests(unittest.IsolatedAsyncioTestCase):
    def _row(self, message_id=None):
        return {"id": "a-1", "message_id": message_id, "file_ref": "/x/a.bin"}

    async def test_unsent_attachment_deletes_row_then_file(self):
        cur = FakeCur()
        cur.executed = []
        cur.execute = lambda sql, params=None: cur.executed.append(" ".join(sql.split()))
        with ExitStack() as stack:
            _open_gate(stack, cur)
            stack.enter_context(
                mock.patch.object(ssr.attachments, "get_owned", return_value=self._row())
            )
            removed = stack.enter_context(mock.patch.object(ssr.attachments, "remove_file"))
            out = await ssr.delete_attachment("a-1", mock.Mock())
        self.assertEqual(out, {"ok": True})
        self.assertTrue(any("DELETE FROM steward_attachments" in s for s in cur.executed))
        removed.assert_called_once_with("/x/a.bin")

    async def test_sent_attachment_is_409(self):
        # 已随消息送出 = 对话留痕,删它等于改历史。
        with ExitStack() as stack:
            _open_gate(stack)
            stack.enter_context(
                mock.patch.object(
                    ssr.attachments, "get_owned", return_value=self._row(message_id="m-1")
                )
            )
            with self.assertRaises(HTTPException) as ctx:
                await ssr.delete_attachment("a-1", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "steward.attachment_bound")

    async def test_someone_elses_attachment_is_404(self):
        with ExitStack() as stack:
            _open_gate(stack)
            stack.enter_context(mock.patch.object(ssr.attachments, "get_owned", return_value=None))
            with self.assertRaises(HTTPException) as ctx:
                await ssr.delete_attachment("a-x", mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)


class BudgetTests(unittest.IsolatedAsyncioTestCase):
    async def test_ownership_checked_before_numbers(self):
        with ExitStack() as stack:
            _open_gate(stack)
            stack.enter_context(mock.patch.object(sc.store, "get_session", return_value=None))
            snap = stack.enter_context(mock.patch.object(ssr.budget, "snapshot"))
            with self.assertRaises(HTTPException) as ctx:
                await ssr.get_budget(mock.Mock(), session_id="s-other")
        self.assertEqual(ctx.exception.status_code, 404)
        snap.assert_not_called()

    async def test_snapshot_passthrough(self):
        payload = {
            "available": True,
            "session": {"spent_thb": "1.20", "cap_thb": "12.00"},
            "tenant_day": {"spent_thb": "3.00", "cap_thb": "150.00"},
        }
        with ExitStack() as stack:
            _open_gate(stack)
            stack.enter_context(mock.patch.object(sc.store, "get_session", return_value=_SESSION))
            stack.enter_context(mock.patch.object(ssr.budget, "snapshot", return_value=payload))
            out = await ssr.get_budget(mock.Mock(), session_id="s-1")
        self.assertEqual(out, payload)


class BudgetSnapshotTests(unittest.TestCase):
    """budget.snapshot 本体:数字口径(两位小数字符串)与 fail-honest。"""

    def test_shape_and_display(self):
        from services.steward import budget

        class Cur:
            def execute(self, *a, **k):
                pass

            def fetchone(self):
                return {"session_spent": "1.234567", "tenant_spent": "10"}

        with (
            mock.patch.object(budget, "ensure_once"),
            mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(Cur())),
        ):
            out = budget.snapshot(tenant_id="t-1", session_id="s-1")
        self.assertTrue(out["available"])
        self.assertEqual(out["session"]["spent_thb"], "1.23")
        self.assertEqual(out["session"]["cap_thb"], "12.00")
        self.assertEqual(out["tenant_day"]["cap_thb"], "150.00")

    def test_infra_failure_reports_unavailable(self):
        from services.steward import budget

        def boom(*a, **k):
            raise RuntimeError("db down")

        with (
            mock.patch.object(budget, "ensure_once"),
            mock.patch("core.db.get_cursor", boom),
        ):
            out = budget.snapshot(tenant_id="t-1", session_id="s-1")
        self.assertEqual(out, {"available": False})


if __name__ == "__main__":
    unittest.main()
