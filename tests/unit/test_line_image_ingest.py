# -*- coding: utf-8 -*-
"""LINE 图片置信驱动入账 ingest_line_image(docs/smart-intake/15 §1)。

锁:低置信→inbox 不建单;高置信齐全→建单 + post_doc(已入账);重复→建草稿不过账(dup);
低 band→建草稿请确认(confirm)。create/post 是否被调按档位精确断言。
"""

import unittest
from unittest import mock

from services.purchase import intake as ik
from services.purchase import line_ingest as li


def _draft():
    return {
        "doc_kind": "purchase_invoice",
        "supplier": {"name": "ACME", "tax_id": None},
        "doc_no": "INV-1",
        "lines": [{"description": "x", "unit_price": "100"}],
        "grand_total": "107.00",
    }


def _run(resolve_ret, *, band="high", auto_book=True):
    created = {"doc": {"id": "D1"}}
    with (
        mock.patch.object(ik, "resolve_image_intake", return_value=resolve_ret),
        mock.patch.object(ik, "workspace_name", return_value="WS"),
        mock.patch(
            "services.purchase.settings.get_settings",
            return_value={"auto_stock_in": False, "auto_book": auto_book},
        ),
        mock.patch("services.purchase.categories.get_tree", return_value=[]),
        mock.patch("services.purchase.docs.create_doc", return_value=created) as cdoc,
        mock.patch("services.purchase.posting.post_doc", return_value=created) as pdoc,
        mock.patch.object(ik, "_stash_inbox") as stash,
    ):
        out = li.ingest_line_image(
            object(),
            tenant_id="t",
            workspace_client_id=1,
            fields={"document_type": "", "seller_name": "ACME", "date": "2026-06-14"},
            confidence=band,
            created_by="u",
        )
    return out, cdoc, pdoc, stash


class IngestTests(unittest.TestCase):
    def test_inbox_no_doc(self):
        res = {"route": "inbox", "draft": None, "dedupe_hit": False, "field_confidence": {}}
        out, cdoc, pdoc, _ = _run(res)
        self.assertEqual(out["state"], "inbox")
        cdoc.assert_not_called()
        pdoc.assert_not_called()

    def test_high_complete_posts(self):
        # 自动入账开 + 高置信齐全 → 直接过账(posted)。
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        out, cdoc, pdoc, _ = _run(res, band="high", auto_book=True)
        self.assertEqual(out["state"], "posted")
        self.assertEqual(out["card_fields"]["detail"], "x")  # 逐条明细填进卡
        cdoc.assert_called_once()
        pdoc.assert_called_once()
        self.assertEqual(out["doc_id"], "D1")

    def test_autobook_off_confirms_no_post(self):
        # 自动入账关(默认):即便高置信齐全也只建草稿发确认卡,不过账。
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        out, cdoc, pdoc, _ = _run(res, band="high", auto_book=False)
        self.assertEqual(out["state"], "confirm")
        cdoc.assert_called_once()
        pdoc.assert_not_called()

    def test_duplicate_confirms_no_post(self):
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": True, "field_confidence": {}}
        out, cdoc, pdoc, _ = _run(res, band="high")
        self.assertEqual(out["state"], "dup")
        cdoc.assert_called_once()
        pdoc.assert_not_called()

    def test_low_band_confirms_no_post(self):
        res = {"route": "purchase", "draft": _draft(), "dedupe_hit": False, "field_confidence": {}}
        out, cdoc, pdoc, _ = _run(res, band="needs_review")
        self.assertEqual(out["state"], "confirm")
        cdoc.assert_called_once()
        pdoc.assert_not_called()

    def test_sales_route_stashed_inbox(self):
        res = {"route": "sales", "draft": None, "dedupe_hit": False, "field_confidence": {}}
        out, cdoc, pdoc, stash = _run(res)
        self.assertEqual(out["state"], "inbox")
        stash.assert_called_once()  # sales 不丢 → 落待归类安全网


if __name__ == "__main__":
    unittest.main()
