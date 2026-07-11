# -*- coding: utf-8 -*-
"""webhook 客户绑定码接线点(routes/line_webhook_routes._handle_line_text)回归契约。

证既有用户 6 位码判定零改动全绿(D2 施工契约断言#4):命中用户码时新分支根本
不被问询;未命中时新分支被问询一次,分支说"没接住"就落回既有 bind_invalid 回落
(现状路径不变)。分支内部逻辑见 test_line_client_bind_intake.py,这里只测接线。
"""

import unittest
from unittest.mock import patch

from routes import line_webhook_routes as w


class ExistingUserCodeFlowRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_user_code_never_consults_client_branch(self):
        with (
            patch.object(w.line_reply, "begin_loading"),
            patch.object(w.db, "get_user_by_line_user_id", return_value=None),
            patch.object(w.db, "consume_line_binding_code", return_value="user-1"),
            patch.object(
                w.db, "find_user_by_id", return_value={"preferred_lang": "en", "tenant_id": "t-1"}
            ),
            patch.object(w.line_client, "get_user_profile", return_value={}),
            patch.object(w.db, "create_or_update_line_binding", return_value=True),
            patch.object(w.line_imagemap, "welcome_messages", return_value=[]),
            patch.object(w.line_reply, "reply_messages_context") as reply_ok,
            patch("services.line_binding.line_client_bind_intake.try_consume") as client_branch,
        ):
            await w._handle_line_text("U-1", "rt", "123456", {"source": {"userId": "U-1"}})
        client_branch.assert_not_called()  # 命中用户码 → 新分支根本不被问询
        reply_ok.assert_called_once()  # 走既有绑定成功回执

    async def test_invalid_code_falls_back_to_existing_bind_invalid(self):
        """非用户码也不是客户码(闸关/查无)→ 落回既有「链接失效」提示,现状零回归。"""
        with (
            patch.object(w.line_reply, "begin_loading"),
            patch.object(w.db, "get_user_by_line_user_id", return_value=None),
            patch.object(w.db, "consume_line_binding_code", return_value=None),
            patch(
                "services.line_binding.line_client_bind_intake.try_consume", return_value=False
            ) as client_branch,
            patch.object(w, "_reply_card_or_text") as reply,
        ):
            await w._handle_line_text("U-1", "rt", "654321", {"source": {"userId": "U-1"}})
        client_branch.assert_called_once()
        reply.assert_called_once()
        self.assertEqual(reply.call_args.args[1], "bind_invalid")


if __name__ == "__main__":
    unittest.main()
