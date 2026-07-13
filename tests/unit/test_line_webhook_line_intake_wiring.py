# -*- coding: utf-8 -*-
"""webhook 收料接线点(routes/line_webhook_routes)· LN-1 回归契约。

守门断言:收料分支说「没接住」(闸关/未绑定统一返 False)时,图片/文件消息的既有
路径逐字节不变——未绑定回 image_not_bound、已绑定照旧进 OCR 队列;接住(True)则
早退,OCR / 未绑定提示一个都不再流动。文字绑定码接线只多传 group_id,单聊传 None。
分支内部逻辑见 test_line_intake_staging.py,这里只测接线。
"""

import unittest
from unittest.mock import AsyncMock, patch

from routes import line_webhook_routes as w


def _image_event(source):
    return {
        "type": "message",
        "replyToken": "rt-1",
        "source": source,
        "message": {"type": "image", "id": "mid-1", "quoteToken": "qt-1"},
    }


class ImageBranchRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_stage_declined_unbound_user_still_gets_not_bound_reply(self):
        """闸关零流动:分支返 False(闸关时必然)→ 未绑定现状提示原样发。"""
        with (
            patch(
                "services.line_binding.line_intake_staging.try_stage_media",
                new=AsyncMock(return_value=False),
            ) as stage,
            patch.object(w.db, "get_user_by_line_user_id", return_value=None),
            patch.object(w.line_reply, "begin_loading"),
            patch.object(w, "_reply_card_or_text") as reply,
        ):
            await w._handle_line_event(_image_event({"type": "user", "userId": "U-1"}))
        stage.assert_awaited_once()
        reply.assert_called_once()
        self.assertEqual(reply.call_args.args[1], "image_not_bound")

    async def test_stage_declined_bound_user_still_enqueues_ocr(self):
        """闸关零流动:分支返 False → 已绑定用户的图照旧进 OCR 队列。"""
        bound = {"id": "u-1", "tenant_id": "t-1"}
        with (
            patch(
                "services.line_binding.line_intake_staging.try_stage_media",
                new=AsyncMock(return_value=False),
            ),
            patch.object(w.db, "get_user_by_line_user_id", return_value=bound),
            patch("services.expense.line_lang.card_lang", return_value="th"),
            patch.object(w.line_reply, "reply_text_context"),
            patch("services.ocr.line_ocr_jobs.enqueue_job", return_value=None) as enqueue,
            patch(
                "services.ocr.line_image_ocr.process_line_image_serial", new=AsyncMock()
            ) as serial,
        ):
            await w._handle_line_event(_image_event({"type": "user", "userId": "U-1"}))
        enqueue.assert_called_once()
        serial.assert_called_once()  # enqueue 返 None 走串行回落(既有路径)

    async def test_stage_accepted_short_circuits_existing_paths(self):
        with (
            patch(
                "services.line_binding.line_intake_staging.try_stage_media",
                new=AsyncMock(return_value=True),
            ),
            patch.object(w.db, "get_user_by_line_user_id") as lookup,
            patch("services.ocr.line_ocr_jobs.enqueue_job") as enqueue,
            patch.object(w, "_reply_card_or_text") as reply,
        ):
            await w._handle_line_event(_image_event({"type": "group", "groupId": "G-1"}))
        lookup.assert_not_called()
        enqueue.assert_not_called()
        reply.assert_not_called()


class TextBindCodeWiringTests(unittest.IsolatedAsyncioTestCase):
    async def _run(self, source):
        with (
            patch.object(w.line_reply, "begin_loading"),
            patch.object(w.db, "get_user_by_line_user_id", return_value=None),
            patch.object(w.db, "consume_line_binding_code", return_value=None),
            patch(
                "services.line_binding.line_client_bind_intake.try_consume", return_value=True
            ) as consume,
        ):
            ev = {"source": source}
            await w._handle_line_text("U-1", "rt", "654321", ev)
        return consume

    async def test_group_source_passes_group_id(self):
        consume = await self._run({"type": "group", "groupId": "G-1", "userId": "U-1"})
        self.assertEqual(consume.call_args.kwargs["group_id"], "G-1")

    async def test_dm_source_passes_none_group_id(self):
        consume = await self._run({"type": "user", "userId": "U-1"})
        self.assertIsNone(consume.call_args.kwargs["group_id"])


if __name__ == "__main__":
    unittest.main()
