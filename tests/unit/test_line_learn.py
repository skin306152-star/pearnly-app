# -*- coding: utf-8 -*-
"""分类学习按钮(Phase B-1)单测:改分类后追发按钮 + postback 按 scope 写规则 + 幂等 + 不拖垮主流程。"""

from __future__ import annotations

import json
import os
import sys
import unittest
from unittest import mock

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.expense import conversation  # noqa: E402
from services.expense import line_correct_data as lcd  # noqa: E402
from services.expense import line_learn  # noqa: E402
from services.line_binding import line_action_nonce, line_client, line_reply  # noqa: E402
from services.purchase import categories as cat_svc  # noqa: E402
from services.purchase import docs as docs_svc  # noqa: E402

_TREE = [{"id": "c1", "name": "商品", "children": [{"id": "s1", "name": "饮料"}]}]


class _Cur:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _detail(seller="tops", cid="c1", sid="s1", desc="tops 水"):
    return {
        "doc": {"category_id": cid, "category_name": "商品"},
        "supplier": {"name": seller, "tax_id": ""},
        "lines": [{"description": desc, "category_id": cid, "subcategory_id": sid}],
    }


class OfferTests(unittest.TestCase):
    def _offer(self, detail):
        pushed, minted = [], {}

        def _mint(cur, *, tenant_id, workspace_client_id, action_ref, user_id="", **k):
            minted["ref"] = action_ref
            return "TOK"

        with (
            mock.patch.object(line_learn.db, "get_cursor_rls", return_value=_Cur()),
            mock.patch.object(docs_svc, "get_doc", return_value=detail),
            mock.patch.object(cat_svc, "get_tree", return_value=_TREE),
            mock.patch.object(line_action_nonce, "mint", side_effect=_mint),
            mock.patch.object(line_client, "push_messages", side_effect=lambda u, m: pushed.append(m)),
        ):
            line_learn.offer("t", 1, "u1", "zh", doc_id="D1")
        return pushed, minted

    def _buttons(self, pushed):
        return pushed[0][0]["contents"]["footer"]["contents"]

    def test_with_vendor_3_buttons(self):
        pushed, minted = self._offer(_detail(seller="tops"))
        self.assertEqual(len(self._buttons(pushed)), 3)  # 仅这次 / 这家 / 这套账
        payload = json.loads(minted["ref"])
        self.assertEqual(payload["vendor"], "tops")
        self.assertEqual(payload["item"], "水")  # 「tops 水」去卖家 → 「水」
        self.assertEqual(payload["cid"], "c1")

    def test_no_vendor_2_buttons(self):
        pushed, _ = self._offer(_detail(seller=""))
        self.assertEqual(len(self._buttons(pushed)), 2)  # 无「这家」按钮

    def test_no_category_no_push(self):
        pushed, _ = self._offer(_detail(cid=None))
        self.assertEqual(pushed, [])  # 没分类不打扰


class PostbackTests(unittest.TestCase):
    def _run(self, scope, payload):
        learned, lcat, replies = [], [], []

        def _consume(cur, *, tenant_id, token):
            return {"status": "ok", "action_ref": json.dumps(payload), "workspace_client_id": 1}

        with (
            mock.patch.object(line_learn.db, "get_cursor_rls", return_value=_Cur()),
            mock.patch.object(line_action_nonce, "consume", side_effect=_consume),
            mock.patch.object(conversation, "learn", side_effect=lambda *a, **k: learned.append(k)),
            mock.patch.object(lcd, "learn_category", side_effect=lambda *a, **k: lcat.append(k)),
            mock.patch.object(line_reply, "reply_text_context", side_effect=lambda t, b, **k: replies.append(b)),
        ):
            line_learn.handle_postback(
                {"tenant_id": "t", "line_user_id": "u1"}, "rt", scope, "TOK", "zh"
            )
        return learned, lcat, replies

    _PAYLOAD = {
        "cid": "c1", "sid": "s1", "cat": "商品", "sub": "饮料",
        "vendor": "tops", "item": "水", "tax": "",
    }

    def test_vendor_writes_text_keyword_and_seller_key(self):
        learned, lcat, replies = self._run("vendor", self._PAYLOAD)
        self.assertTrue(any(k.get("keyword") == "tops" for k in learned))  # 文字路卖家关键词
        self.assertEqual(len(lcat), 1)  # 图片路 learn_category(seller:/tax:)
        self.assertIn("tops", replies[0])
        self.assertIn("商品", replies[0])

    def test_ws_writes_item_keyword(self):
        learned, lcat, replies = self._run("ws", self._PAYLOAD)
        self.assertTrue(any(k.get("keyword") == "水" for k in learned))  # 品名关键词(跨卖家)
        self.assertEqual(len(lcat), 0)  # ws 不写 seller 键
        self.assertIn("水", replies[0])

    def test_once_writes_nothing(self):
        learned, lcat, replies = self._run("once", self._PAYLOAD)
        self.assertEqual(learned, [])
        self.assertEqual(lcat, [])
        self.assertEqual(replies, [line_learn.ci.t(line_learn.ci.LEARN_ONCE, "zh")])

    def test_idempotent_used_token_no_write(self):
        replies = []

        def _consume(cur, *, tenant_id, token):
            return {"status": "used", "action_ref": "{}", "workspace_client_id": 1}

        with (
            mock.patch.object(line_learn.db, "get_cursor_rls", return_value=_Cur()),
            mock.patch.object(line_action_nonce, "consume", side_effect=_consume),
            mock.patch.object(conversation, "learn") as learn,
            mock.patch.object(line_reply, "reply_text_context", side_effect=lambda t, b, **k: replies.append(b)),
        ):
            line_learn.handle_postback({"tenant_id": "t", "line_user_id": "u1"}, "rt", "vendor", "TOK", "zh")
        learn.assert_not_called()  # ★重复点不重复写
        self.assertEqual(replies, [line_learn.ci.t(line_learn.ci.LEARN_STALE, "zh")])

    def test_exception_swallowed_friendly_reply(self):
        replies = []
        with (
            mock.patch.object(line_learn.db, "get_cursor_rls", return_value=_Cur()),
            mock.patch.object(line_action_nonce, "consume", side_effect=RuntimeError("boom")),
            mock.patch.object(line_reply, "reply_text_context", side_effect=lambda t, b, **k: replies.append(b)),
        ):
            line_learn.handle_postback({"tenant_id": "t", "line_user_id": "u1"}, "rt", "ws", "TOK", "zh")
        self.assertEqual(replies, [line_learn.ci.t(line_learn.ci.LEARN_STALE, "zh")])  # 不抛·友好兜底


class LearnedAppliedNextTimeTests(unittest.TestCase):
    """学到的关键词被文字路 lookup_learned 命中(验证下次同卖家/同品名自动套用)。"""

    class _LookCur:
        def __init__(self, rows):
            self._rows = rows

        def execute(self, *a, **k):
            pass

        def fetchall(self):
            return self._rows

    def test_vendor_keyword_matches_future_text(self):
        rows = [{"keyword": "tops", "category_id": "c1", "subcategory_id": "s1",
                 "category_name": "商品", "subcategory_name": "饮料"}]
        hit = conversation.lookup_learned(
            self._LookCur(rows), tenant_id="t", workspace_client_id=1, text="tops 水 20"
        )
        self.assertEqual(hit["category_id"], "c1")  # 「tops 水 20」命中学到的 tops→商品

    def test_item_keyword_matches_across_vendors(self):
        rows = [{"keyword": "水", "category_id": "c1", "subcategory_id": "s1",
                 "category_name": "商品", "subcategory_name": "饮料"}]
        hit = conversation.lookup_learned(
            self._LookCur(rows), tenant_id="t", workspace_client_id=1, text="711 水 15"
        )
        self.assertEqual(hit["category_id"], "c1")  # 品名规则跨卖家命中


if __name__ == "__main__":
    unittest.main()
