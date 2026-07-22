# -*- coding: utf-8 -*-
"""posting_preview 四态 gate 守门 · 纯函数(无 DB)。

ok / confirm_profile / escalate / decide_items 四条路各钉一例;重点验跨类(商品只存在于库存
目录、本客户按非库存落 → cross_kind → decide_items 交人裁)。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.erp.express_push.posting_preview import compute_posting_preview  # noqa: E402

_NONE_FP = {"stock_master_count": 4, "stcrd_lines": 1530, "stcrd_lines_moving_stock": 75}
_PERPETUAL_FP = {"stock_master_count": 672, "stcrd_lines": 9300, "stcrd_lines_moving_stock": 8102}
_CATALOG = [
    {"code": "14-01", "name": "น้ำแข็งหลอด", "kind": "stock"},
    {"code": "PN01", "name": "ค่าบริการ", "kind": "non_stock"},
]


def _cfg(fp=None, profile=None, catalog=_CATALOG):
    c = {"reported_products": catalog}
    if fp:
        c["catalog_fingerprint"] = fp
    if profile:
        c["posting_profile"] = profile
    return c


def _docs(*names):
    return [{"history_id": "h", "items": [{"name": n} for n in names]}]


class PreviewGateTests(unittest.TestCase):
    def test_ok_new_item_none_client(self):
        r = compute_posting_preview(_docs("สินค้าใหม่ไม่มีในระบบ"), _cfg(_NONE_FP))
        self.assertEqual(r["gate"], "ok")
        self.assertEqual(r["summary"]["new"], 1)

    def test_ok_reuse_non_stock(self):
        r = compute_posting_preview(_docs("ค่าบริการ"), _cfg(_NONE_FP))
        self.assertEqual(r["gate"], "ok")
        self.assertEqual(r["summary"]["reuse"], 1)

    def test_decide_items_cross_kind_stock_only(self):
        # 商品只存在于库存目录,本客户按非库存落 → cross_kind → 交人裁。
        r = compute_posting_preview(_docs("น้ำแข็งหลอด"), _cfg(_NONE_FP))
        self.assertEqual(r["gate"], "decide_items")
        self.assertTrue(r["items"][0]["cross_kind"])
        self.assertEqual(r["items"][0]["kind"], "stock")

    def test_decide_items_fuzzy(self):
        cat = [{"code": "P1", "name": "ABCDEFGHIJ", "kind": "non_stock"}]
        r = compute_posting_preview(_docs("ABCDEFGHIX"), _cfg(_NONE_FP, catalog=cat))
        self.assertEqual(r["gate"], "decide_items")
        self.assertEqual(r["summary"]["confirm"], 1)

    def test_confirm_profile_when_no_fingerprint(self):
        r = compute_posting_preview(_docs("อะไรก็ได้"), {"reported_products": _CATALOG})
        self.assertEqual(r["gate"], "confirm_profile")

    def test_escalate_perpetual_without_stock_lane(self):
        r = compute_posting_preview(_docs("x"), _cfg(_PERPETUAL_FP))
        self.assertEqual(r["gate"], "escalate")

    def test_confirmed_override_suppresses_confirm(self):
        cfg = _cfg(_NONE_FP, profile={"posting_mode": "non_stock", "inventory_usage": "none"})
        r = compute_posting_preview(_docs("สินค้าใหม่"), cfg)
        self.assertEqual(r["gate"], "ok")
        self.assertEqual(r["profile"]["source"], "confirmed")

    def test_empty_docs_ok(self):
        r = compute_posting_preview([], _cfg(_NONE_FP))
        self.assertEqual(r["gate"], "ok")
        self.assertEqual(r["summary"], {"reuse": 0, "new": 0, "confirm": 0})


if __name__ == "__main__":
    unittest.main()
