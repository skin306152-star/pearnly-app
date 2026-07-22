# -*- coding: utf-8 -*-
"""销售明细导出「新建/复用」动作回填 · 纯逻辑单测(解析 response_body + 填 merged_fields)。

DAL(erp_actions_by_*)是薄 SQL,由 E2E 覆盖;此处钉死解析与应用不出错(顺序/缺字段/坏输入)。
"""

import json
import unittest

from services.erp.export_actions import _parse_erp_actions, apply_erp_actions


class ParseErpActions(unittest.TestCase):
    def test_dict_body_customer_new_and_line_created(self):
        body = {
            "ok": True,
            "line_modes": [
                {"seq": 2, "name": "b", "created": False},
                {"seq": 1, "name": "a", "created": True},
            ],
            "meta": {"created_customer": True},
        }
        got = _parse_erp_actions(body)
        self.assertTrue(got["customer"])
        # 按 seq 升序对齐 → [True(seq1), False(seq2)]
        self.assertEqual(got["items"], [True, False])

    def test_json_string_body(self):
        body = json.dumps(
            {"line_modes": [{"seq": 1, "created": None}], "meta": {"created_customer": False}}
        )
        got = _parse_erp_actions(body)
        self.assertFalse(got["customer"])
        self.assertEqual(got["items"], [None])

    def test_missing_meta_and_line_modes(self):
        got = _parse_erp_actions({"ok": True})
        self.assertIsNone(got["customer"])
        self.assertEqual(got["items"], [])

    def test_garbage_body_degrades_empty(self):
        got = _parse_erp_actions("not json at all")
        self.assertIsNone(got["customer"])
        self.assertEqual(got["items"], [])

    def test_created_customer_non_bool_becomes_none(self):
        got = _parse_erp_actions({"meta": {"created_customer": "yes"}})
        self.assertIsNone(got["customer"])


class ApplyErpActions(unittest.TestCase):
    def test_fills_customer_and_items(self):
        mf = {"invoice_number": "IV1", "items": [{"name": "a"}, {"name": "b"}]}
        apply_erp_actions(mf, {"customer": True, "items": [True, False]})
        self.assertEqual(mf["customer_erp_action"], "new")
        self.assertEqual(mf["items"][0]["erp_action"], "new")
        self.assertEqual(mf["items"][1]["erp_action"], "reused")

    def test_customer_reused(self):
        mf = {"items": []}
        apply_erp_actions(mf, {"customer": False, "items": []})
        self.assertEqual(mf["customer_erp_action"], "reused")

    def test_none_action_is_noop(self):
        mf = {"items": [{"name": "a"}]}
        apply_erp_actions(mf, None)
        self.assertNotIn("customer_erp_action", mf)
        self.assertNotIn("erp_action", mf["items"][0])

    def test_line_created_none_leaves_item_untouched(self):
        mf = {"items": [{"name": "a"}]}
        apply_erp_actions(mf, {"customer": None, "items": [None]})
        self.assertNotIn("erp_action", mf["items"][0])
        self.assertNotIn("customer_erp_action", mf)

    def test_more_items_than_line_modes_only_fills_matched(self):
        mf = {"items": [{"name": "a"}, {"name": "b"}, {"name": "c"}]}
        apply_erp_actions(mf, {"customer": True, "items": [True]})
        self.assertEqual(mf["items"][0]["erp_action"], "new")
        self.assertNotIn("erp_action", mf["items"][1])
        self.assertNotIn("erp_action", mf["items"][2])


if __name__ == "__main__":
    unittest.main()
