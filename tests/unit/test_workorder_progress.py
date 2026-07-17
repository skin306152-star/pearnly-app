# -*- coding: utf-8 -*-
"""services/workorder/progress.py 守门(J-B · api.py 拆分产物,铁律 #27.1)。

直接测两个纯函数(不经 api.order_detail 间接覆盖)——classify_progress/bank_progress
零 DB 依赖,纯 dict 现算,脱管单测最省事。api.order_detail() 的整合行为(键名/降级 None)
仍由 tests/unit/test_workorder_api.py 的 ClassifyProgressTests/BankProgressTests 守,
两处不重复断言同一件事,这里只管这两个函数本身算得对不对。
"""

from __future__ import annotations

import unittest

from services.workorder import progress


class ClassifyProgressTests(unittest.TestCase):
    def _images(self):
        return [
            {"id": f"img-{i}", "file_ref": f"/x/IMG_{i}.jpg"} for i in range(3)
        ] + [{"id": "xlsx-1", "file_ref": "/x/sales.xlsx"}]

    def test_counts_classified_images_during_classify_step(self):
        out = progress.classify_progress(
            {"current_step": "classify"},
            self._images(),
            {"img-0": {}, "img-1": {}},
        )
        self.assertEqual(out, {"step": "classify", "processed": 2, "total": 3})

    def test_none_outside_classify_step(self):
        out = progress.classify_progress({"current_step": "reconcile"}, self._images(), {})
        self.assertIsNone(out)

    def test_none_when_no_image_items(self):
        out = progress.classify_progress(
            {"current_step": "classify"}, [{"id": "xlsx-1", "file_ref": "/x/sales.xlsx"}], {}
        )
        self.assertIsNone(out)


class BankProgressTests(unittest.TestCase):
    def _bank_items(self):
        return [
            {"id": f"bank-{i}", "kind": "bank_statement", "file_ref": f"/x/stmt_{i}.pdf"}
            for i in range(3)
        ] + [{"id": "inv-1", "kind": "purchase_invoice", "file_ref": "/x/inv.jpg"}]

    def test_counts_parsed_banks_during_reconcile_step(self):
        out = progress.bank_progress(
            {"current_step": "reconcile"}, self._bank_items(), {"bank-0": {}}
        )
        self.assertEqual(out, {"step": "reconcile", "processed": 1, "total": 3})

    def test_none_outside_reconcile_step(self):
        out = progress.bank_progress({"current_step": "classify"}, self._bank_items(), {})
        self.assertIsNone(out)

    def test_none_when_no_bank_items(self):
        out = progress.bank_progress(
            {"current_step": "reconcile"},
            [{"id": "inv-1", "kind": "purchase_invoice", "file_ref": "/x/inv.jpg"}],
            {},
        )
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
