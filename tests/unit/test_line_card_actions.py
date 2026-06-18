# -*- coding: utf-8 -*-
"""卡片动作落地:confirm→post_doc、undo→void_doc、非法/异常→友好回执(docs/smart-intake/15 §4)。"""

import unittest
from unittest import mock

from services.line_binding import line_card_actions as lca
from services.line_binding import line_postback


class _CM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _detail(status="posted"):
    return {
        "doc": {"id": "D1", "grand_total": "190.00", "status": status},
        "supplier": {},
        "lines": [],
    }


def _run(data, *, ws=1, post_doc_side=None, get_doc_ret=None):
    sent = []
    from core import db
    from services.expense import line_correct
    from services.line_binding import line_client

    doc = _detail()
    post_kw = {"side_effect": post_doc_side} if post_doc_side else {"return_value": doc}
    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM()),
        mock.patch("core.workspace_context.default_workspace_id", return_value=ws),
        mock.patch(
            "services.purchase.settings.get_settings", return_value={"auto_stock_in": False}
        ),
        mock.patch("services.purchase.posting.post_doc", **post_kw) as post_doc,
        mock.patch("services.purchase.posting.void_doc", return_value=doc) as void_doc,
        mock.patch("services.purchase.docs.delete_doc") as delete_doc,
        mock.patch("services.purchase.docs.get_doc", return_value=get_doc_ret or doc),
        mock.patch.object(line_correct, "_set_active"),
        mock.patch.object(
            lca.line_reply,
            "reply_text_context",
            side_effect=lambda rt, b, **k: sent.append(b) or True,
        ),
        mock.patch.object(
            lca.line_reply,
            "reply_messages_context",
            side_effect=lambda rt, msgs, **k: sent.append(msgs) or True,
        ),
        mock.patch.object(
            line_client,
            "t_line",
            side_effect=lambda lang, key, **kw: f"{key}:{kw.get('amount','')}",
        ),
    ):
        lca.handle_postback({"tenant_id": "t", "id": "u"}, "rt", data, "zh")
        svc = mock.MagicMock(post_doc=post_doc, void_doc=void_doc, delete_doc=delete_doc)
    return sent, svc


class CardActionTests(unittest.TestCase):
    def test_confirm_sends_posted_card(self):
        # P1G 验收 1:确认入账后回 posted 数据卡(状态/金额/查看详情/撤销),不再只是单行文字。
        sent, svc = _run(line_postback.confirm_data("D1"))
        svc.post_doc.assert_called_once()
        card = sent[0][0]
        self.assertEqual(card["type"], "flex")
        self.assertIn("已保存", str(card))
        self.assertIn("190.00", str(card))
        self.assertIn("查看详情", str(card))
        self.assertIn("撤销", str(card))

    def test_double_confirm_no_nonce_reshows_posted_no_repost(self):
        # P1G 验收 2:无 token 重复确认(单已 posted)→ post_doc 抛 not_draft → 重发 posted 卡,
        # 不重复入账、不报错。
        from core.pos_api import PosError

        def _raise(*a, **k):
            raise PosError("purchase.not_draft", 409, detail="not_draft")

        sent, svc = _run(line_postback.confirm_data("D1"), post_doc_side=_raise)
        card = sent[0][0]
        self.assertEqual(card["type"], "flex")
        self.assertIn("已保存", str(card))

    def test_undo_sends_voided_terminal_card(self):
        # P1D:撤销后回「已撤销」终态卡(Flex·含查看记录),不再纯文字。
        sent, svc = _run(line_postback.undo_data("D1"))
        svc.void_doc.assert_called_once()
        card = sent[0][0]
        self.assertEqual(card["type"], "flex")
        self.assertIn("已撤销", str(card))
        self.assertIn("查看记录", str(card))

    def test_discard_sends_discarded_terminal_card(self):
        # P1D:丢弃后回「已丢弃」终态卡(草稿已删→无可执行动作·无 footer)。
        sent, svc = _run(line_postback.discard_data("D1"))
        svc.delete_doc.assert_called_once()
        svc.post_doc.assert_not_called()
        card = sent[0][0]
        self.assertEqual(card["type"], "flex")
        self.assertIn("已丢弃", str(card))
        self.assertNotIn("footer", card["contents"])

    def test_bad_data_stale_reply(self):
        sent, svc = _run("garbage")
        svc.post_doc.assert_not_called()
        self.assertTrue(sent[0].startswith("card_action_stale"))

    def test_no_workspace_stale(self):
        sent, svc = _run(line_postback.confirm_data("D1"), ws=None)
        svc.post_doc.assert_not_called()
        self.assertTrue(sent[0].startswith("card_action_stale"))


def _run_token(data, consume_res, *, get_doc_ret=None):
    """带令牌路径:patch nonce.consume 返回受控结果,验证分发/友好回执/重发当前卡。"""
    sent = []
    from core import db
    from services.expense import line_correct
    from services.line_binding import line_action_nonce, line_client

    doc = _detail()
    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM()),
        mock.patch.object(line_action_nonce, "consume", return_value=consume_res) as consume,
        mock.patch(
            "services.purchase.settings.get_settings", return_value={"auto_stock_in": False}
        ),
        mock.patch("services.purchase.posting.post_doc", return_value=doc) as post_doc,
        mock.patch("services.purchase.docs.get_doc", return_value=get_doc_ret or doc),
        mock.patch.object(line_correct, "_set_active"),
        mock.patch.object(
            lca.line_reply,
            "reply_text_context",
            side_effect=lambda rt, b, **k: sent.append(b) or True,
        ),
        mock.patch.object(
            lca.line_reply,
            "reply_messages_context",
            side_effect=lambda rt, msgs, **k: sent.append(msgs) or True,
        ),
        mock.patch.object(
            line_client,
            "t_line",
            side_effect=lambda lang, key, **kw: f"{key}:{kw.get('amount','')}",
        ),
    ):
        lca.handle_postback({"tenant_id": "t", "id": "u"}, "rt", data, "zh")
    return sent, consume, post_doc


class CardActionTokenTests(unittest.TestCase):
    """PO-12:postback 带一次性令牌 → 原子消费防重放;目标记录取自令牌。"""

    def test_token_confirm_consumes_and_posts_nonce_ref(self):
        data = line_postback.confirm_data("ignored", token="TOK")
        res = {"status": "ok", "action_ref": "D9", "workspace_client_id": 7, "user_id": "u"}
        sent, consume, post_doc = _run_token(data, res)
        consume.assert_called_once()
        post_doc.assert_called_once()
        # 服务端用令牌反查的 ref(D9),不信 postback 里的 doc(ignored)
        self.assertEqual(post_doc.call_args.kwargs["doc_id"], "D9")
        card = sent[0][0]  # 回 posted 数据卡
        self.assertEqual(card["type"], "flex")
        self.assertIn("已保存", str(card))

    def test_token_replay_used_reshows_posted(self):
        # P1G 验收 2:令牌已消费(双击重放)+ 单已 posted → 重发 posted 卡,不重复入账、不报错。
        data = line_postback.confirm_data("D9", token="TOK")
        used = {"status": "used", "action_ref": "D9", "workspace_client_id": 7}
        sent, consume, post_doc = _run_token(data, used)
        post_doc.assert_not_called()
        card = sent[0][0]
        self.assertEqual(card["type"], "flex")
        self.assertIn("已保存", str(card))

    def test_token_replay_used_voided_reshows_terminal(self):
        # 撤销后再点(令牌已消费 + 单已 void)→ 回「已撤销」终态卡,不二次处理。
        data = line_postback.undo_data("D9", token="TOK")
        used = {"status": "used", "action_ref": "D9", "workspace_client_id": 7}
        sent, _, post_doc = _run_token(data, used, get_doc_ret=_detail("void"))
        card = sent[0][0]
        self.assertEqual(card["type"], "flex")
        self.assertIn("已撤销", str(card))

    def test_token_expired_friendly(self):
        data = line_postback.confirm_data("D9", token="TOK")
        sent, consume, post_doc = _run_token(data, {"status": "expired"})
        post_doc.assert_not_called()
        self.assertTrue(sent[0].startswith("card_action_expired"))


if __name__ == "__main__":
    unittest.main()
