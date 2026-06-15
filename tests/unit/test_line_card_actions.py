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


def _run(data, *, ws=1):
    sent = []
    from core import db
    from services.line_binding import line_client

    doc = {"doc": {"grand_total": "190.00"}}
    with (
        mock.patch.object(db, "get_cursor_rls", return_value=_CM()),
        mock.patch("core.workspace_context.default_workspace_id", return_value=ws),
        mock.patch(
            "services.purchase.settings.get_settings", return_value={"auto_stock_in": False}
        ),
        mock.patch("services.purchase.posting.post_doc", return_value=doc) as post_doc,
        mock.patch("services.purchase.posting.void_doc", return_value=doc) as void_doc,
        mock.patch("services.purchase.docs.delete_doc") as delete_doc,
        mock.patch(
            "services.purchase.intake.resolve_inbox", return_value={"doc_id": "D9"}
        ) as resolve_inbox,
        mock.patch.object(line_client, "reply_text", side_effect=lambda rt, b: sent.append(b)),
        mock.patch.object(
            line_client,
            "t_line",
            side_effect=lambda lang, key, **kw: f"{key}:{kw.get('amount','')}",
        ),
    ):
        lca.handle_postback({"tenant_id": "t", "id": "u"}, "rt", data, "zh")
        svc = mock.MagicMock(
            post_doc=post_doc,
            void_doc=void_doc,
            delete_doc=delete_doc,
            resolve_inbox=resolve_inbox,
        )
    return sent, svc


class CardActionTests(unittest.TestCase):
    def test_confirm_posts(self):
        sent, svc = _run(line_postback.confirm_data("D1"))
        svc.post_doc.assert_called_once()
        self.assertTrue(sent[0].startswith("card_confirmed:"))

    def test_undo_voids(self):
        sent, svc = _run(line_postback.undo_data("D1"))
        svc.void_doc.assert_called_once()
        self.assertTrue(sent[0].startswith("card_undone:"))

    def test_discard_deletes_draft(self):
        sent, svc = _run(line_postback.discard_data("D1"))
        svc.delete_doc.assert_called_once()
        svc.post_doc.assert_not_called()
        self.assertTrue(sent[0].startswith("card_discarded"))

    def test_inbox_post_resolves_then_posts(self):
        sent, svc = _run(line_postback.inbox_post_data("I7"))
        svc.resolve_inbox.assert_called_once()
        svc.post_doc.assert_called_once()  # 仍要入账 = 建草稿后过账
        self.assertTrue(sent[0].startswith("card_confirmed:"))

    def test_inbox_drop_dismisses(self):
        sent, svc = _run(line_postback.inbox_drop_data("I7"))
        svc.resolve_inbox.assert_called_once()
        svc.post_doc.assert_not_called()
        self.assertTrue(sent[0].startswith("card_discarded"))

    def test_bad_data_stale_reply(self):
        sent, svc = _run("garbage")
        svc.post_doc.assert_not_called()
        self.assertTrue(sent[0].startswith("card_action_stale"))

    def test_no_workspace_stale(self):
        sent, svc = _run(line_postback.confirm_data("D1"), ws=None)
        svc.post_doc.assert_not_called()
        self.assertTrue(sent[0].startswith("card_action_stale"))


if __name__ == "__main__":
    unittest.main()
