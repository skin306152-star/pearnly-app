# -*- coding: utf-8 -*-
"""万能口的两个新端点 + 带附件的一轮对话(routes/steward_routes.py · 编排面)。

锁:①超限/坏料在落盘之前就诚实拒(413/422 带结构化 detail);②别人的附件下不到、
登记过但指向会话之外的路径也下不到;③纯文件手势与按钮点击【一次模型都不调】——
那两条路上 planner 必须零调用(歧义已被一次点击解决,再猜一遍就是把问题重新引进来)。
"""

from __future__ import annotations

import unittest
from contextlib import ExitStack
from unittest import mock

from fastapi import HTTPException

from routes import steward_routes as sr
from services.steward import attach_intake, attachments, orchestrator, store
from services.workorder import intake_prep
from tests.unit._route_contract_fakes import CurCM, FakeCur

_USER = {"id": "u1", "tenant_id": "t-1"}
_SESSION = {"id": "s-1", "tenant_id": "t-1", "user_id": "u1"}


def _open_gate(stack: ExitStack) -> None:
    """登录 + 闸开 + 会话归属命中 + 假游标(编排走真码,只桩边界)。"""
    for patch in (
        mock.patch.object(sr, "authorize_pearnly_ai", return_value=(_USER, "t-1")),
        mock.patch.object(sr.feature_flags, "pearnly_ai_steward_enabled_for", return_value=True),
        mock.patch.object(sr.store, "ensure_once"),
        mock.patch.object(sr.store, "get_session", return_value=_SESSION),
        mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
        mock.patch.object(sr, "_context", return_value=mock.Mock(tenant_id="t-1")),
    ):
        stack.enter_context(patch)


class _Upload:
    def __init__(self, filename, content):
        self.filename = filename
        self._content = content

    async def read(self, size=-1):
        return self._content[:size] if size and size > 0 else self._content


class UploadTests(unittest.IsolatedAsyncioTestCase):
    async def _post(self, files, **over):
        with ExitStack() as stack:
            _open_gate(stack)
            accept = stack.enter_context(mock.patch.object(sr.attach_intake, "accept", **over))
            out = await sr.add_attachments("s-1", mock.Mock(), files=files)
        return out, accept

    async def test_happy_path_returns_the_landed_attachments(self):
        landed = [{"attachment_id": "a-1", "name": "gl.pdf"}]
        out, accept = await self._post([_Upload("gl.pdf", b"%PDF")], return_value=landed)
        self.assertEqual(out, {"attachments": landed, "count": 1})
        self.assertEqual(accept.call_args.kwargs["session_id"], "s-1")
        self.assertEqual(accept.call_args.kwargs["pairs"], [("gl.pdf", b"%PDF")])

    async def test_over_limit_is_413_with_the_number_the_frontend_needs(self):
        err = attach_intake.AttachmentLimitError(attach_intake.ERR_TOO_MANY, 20, 21)
        with self.assertRaises(HTTPException) as ctx:
            await self._post([_Upload("a.pdf", b"x")], side_effect=err)
        self.assertEqual(ctx.exception.status_code, 413)
        self.assertEqual(ctx.exception.detail["code"], attach_intake.ERR_TOO_MANY)
        self.assertEqual(ctx.exception.detail["limit"], 20)
        self.assertEqual(ctx.exception.detail["actual"], 21)

    async def test_unopenable_file_is_422_with_four_language_text(self):
        err = intake_prep.IntakePrepError("workorder.intake.zip_corrupt", filename="a.zip")
        with self.assertRaises(HTTPException) as ctx:
            await self._post([_Upload("a.zip", b"PK")], side_effect=err)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(sorted(ctx.exception.detail["message"]), ["en", "ja", "th", "zh"])
        self.assertEqual(ctx.exception.detail["filename"], "a.zip")

    async def test_reads_at_most_one_byte_past_the_single_file_cap(self):
        """封顶读法:超大文件不整读进内存,超限交给 check_limits 判。"""
        upload = mock.Mock()
        upload.filename = "big.pdf"
        upload.read = mock.AsyncMock(return_value=b"x")
        with ExitStack() as stack:
            _open_gate(stack)
            stack.enter_context(mock.patch.object(sr.attach_intake, "accept", return_value=[]))
            await sr.add_attachments("s-1", mock.Mock(), files=[upload])
        upload.read.assert_awaited_once_with(attachments.MAX_FILE_BYTES + 1)


class DownloadTests(unittest.IsolatedAsyncioTestCase):
    async def _download(self, *patches):
        with ExitStack() as stack:
            _open_gate(stack)
            for patch in patches:
                stack.enter_context(patch)
            return await sr.download_attachment("a-1", mock.Mock())

    async def test_not_mine_is_404(self):
        with self.assertRaises(HTTPException) as ctx:
            await self._download(mock.patch.object(attachments, "get_owned", return_value=None))
        self.assertEqual(ctx.exception.status_code, 404)

    async def test_registered_row_pointing_outside_the_session_is_404(self):
        row = {"id": "a-1", "session_id": "s-1", "file_ref": "/etc/passwd", "original_name": "x"}
        with self.assertRaises(HTTPException) as ctx:
            await self._download(
                mock.patch.object(attachments, "get_owned", return_value=row),
                mock.patch.object(attachments, "resolve_within_session", return_value=None),
            )
        self.assertEqual(ctx.exception.status_code, 404)


class MessageShapeTests(unittest.IsolatedAsyncioTestCase):
    async def _post(self, body, *patches):
        with ExitStack() as stack:
            _open_gate(stack)
            for patch in patches:
                stack.enter_context(patch)
            return await sr.post_message("s-1", body, mock.Mock())

    async def test_nothing_said_and_nothing_attached_is_422(self):
        with self.assertRaises(HTTPException) as ctx:
            await self._post(sr.MessageIn(text="  "))
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, sr._EMPTY_TURN)

    async def test_files_only_turn_is_allowed(self):
        out = await self._post(
            sr.MessageIn(text="", attachment_ids=["a-1"]),
            mock.patch.object(orchestrator, "handle_message", return_value={"reply": "ok"}),
        )
        self.assertEqual(out, {"reply": "ok"})

    async def test_action_carries_its_own_attachment_ids(self):
        handle = mock.patch.object(orchestrator, "handle_message", return_value={})
        with ExitStack() as stack:
            _open_gate(stack)
            spy = stack.enter_context(handle)
            await sr.post_message(
                "s-1",
                sr.MessageIn(
                    action=sr.ActionIn(
                        tool="file_convert", attachment_ids=["a-9"], confirm_spend=True
                    )
                ),
                mock.Mock(),
            )
        kwargs = spy.call_args.kwargs
        self.assertEqual(kwargs["attachment_ids"], ("a-9",))
        self.assertTrue(kwargs["action"]["confirm_spend"])


class NoModelPathTests(unittest.TestCase):
    """万能口的两条不过模型的路:纯文件手势 / 卡上按钮。planner 零调用是硬要求。"""

    _ROWS = [
        {
            "id": "a-1",
            "original_name": "gl.pdf",
            "kind": "gl_ledger",
            "kind_source": "rule",
            "detect": {"page_count": 2, "needs_model": False, "actions": ["file_convert"]},
            "size_bytes": 10,
        }
    ]

    def _run(self, **over):
        with ExitStack() as stack:
            for patch in (
                mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
                mock.patch.object(orchestrator, "_attachment_rows", return_value=self._ROWS),
                mock.patch.object(store, "add_message", return_value={"id": "m-1"}),
                mock.patch.object(store, "set_title_if_empty"),
                mock.patch.object(store, "touch_session"),
                mock.patch.object(store, "list_messages", return_value=[]),
                mock.patch.object(store, "create_task", return_value={"id": "task-1"}),
                mock.patch.object(store, "finish_task", return_value=True),
                mock.patch.object(attachments, "attach_to_message", return_value=1),
            ):
                stack.enter_context(patch)
            plan = stack.enter_context(mock.patch.object(orchestrator.planner, "plan"))
            reserve = stack.enter_context(mock.patch.object(orchestrator.budget, "reserve"))
            ctx = mock.Mock(tenant_id="t-1", user_id="u1", lang="zh", allowed_client_ids=None)
            out = orchestrator.handle_message(ctx, session_id="s-1", **over)
        return out, plan, reserve

    def test_files_only_turn_never_calls_the_planner(self):
        out, plan, reserve = self._run(text="", attachment_ids=("a-1",))
        plan.assert_not_called()
        reserve.assert_not_called()
        self.assertEqual(out["task_status"], store.TASK_RUNNING)  # 唯一零成本动作 → 直接跑
        self.assertEqual(out["attachments"][0]["attachment_id"], "a-1")

    def test_button_click_never_calls_the_planner(self):
        out, plan, _ = self._run(
            text="",
            attachment_ids=("a-1",),
            action={"tool": "file_convert", "attachment_ids": ["a-1"], "confirm_spend": False},
        )
        plan.assert_not_called()
        self.assertEqual(out["task_status"], store.TASK_RUNNING)

    def test_a_tool_name_outside_the_closed_set_gets_no_task(self):
        """按钮上的工具名是客户端来的,当不可信输入:闭集外一律派不出活。"""
        out, plan, _ = self._run(
            text="",
            attachment_ids=("a-1",),
            action={"tool": "erp_push", "attachment_ids": ["a-1"], "confirm_spend": True},
        )
        plan.assert_not_called()
        self.assertIsNone(out.get("task_id"))


if __name__ == "__main__":
    unittest.main()
