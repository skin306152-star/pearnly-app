# -*- coding: utf-8 -*-
"""置信入账编排归一(PO-11):文/图共用 book_by_confidence,auto_book 统一裁决过账。"""

import unittest
from unittest import mock

from services.purchase import confidence_post


class _Verdict:
    def __init__(self, action, dup=False):
        self.action = action
        self.dup = dup


def _run(verdict, settings):
    created = {"doc": {"id": "D1"}}
    with (
        mock.patch("services.purchase.docs.create_doc", return_value=created) as cdoc,
        mock.patch("services.purchase.posting.post_doc", return_value=created) as pdoc,
    ):
        out = confidence_post.book_by_confidence(
            object(),
            tenant_id="t",
            workspace_client_id=1,
            data={"doc_kind": "expense"},
            settings=settings,
            verdict=verdict,
            created_by="u",
        )
    return out, cdoc, pdoc


class BookByConfidenceTests(unittest.TestCase):
    def test_post_when_high_and_auto_book_on(self):
        (doc_id, state), cdoc, pdoc = _run(_Verdict("post"), {"auto_book": True})
        self.assertEqual((doc_id, state), ("D1", "posted"))
        cdoc.assert_called_once()
        pdoc.assert_called_once()

    def test_confirm_when_auto_book_off(self):
        # auto_book 关 → 即便高置信也只建草稿(确认优先)。
        (doc_id, state), cdoc, pdoc = _run(_Verdict("post"), {"auto_book": False})
        self.assertEqual(state, "confirm")
        pdoc.assert_not_called()

    def test_dup_never_posts(self):
        (_id, state), _c, pdoc = _run(_Verdict("confirm", dup=True), {"auto_book": True})
        self.assertEqual(state, "dup")
        pdoc.assert_not_called()

    def test_low_confidence_confirm(self):
        (_id, state), _c, pdoc = _run(_Verdict("confirm"), {"auto_book": True})
        self.assertEqual(state, "confirm")
        pdoc.assert_not_called()

    def test_auto_stock_in_passed_through(self):
        with (
            mock.patch("services.purchase.docs.create_doc", return_value={"doc": {"id": "D1"}}),
            mock.patch("services.purchase.posting.post_doc", return_value={}) as pdoc,
        ):
            confidence_post.book_by_confidence(
                object(),
                tenant_id="t",
                workspace_client_id=1,
                data={},
                settings={"auto_book": True, "auto_stock_in": True},
                verdict=_Verdict("post"),
                created_by="u",
            )
        self.assertIs(pdoc.call_args.kwargs["auto_stock_in"], True)


if __name__ == "__main__":
    unittest.main()
