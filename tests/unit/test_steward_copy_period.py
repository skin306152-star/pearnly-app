# -*- coding: utf-8 -*-
"""本期盘点两问的文案与左窗产物(copy_period + copy_artifacts · B2 形状契约)。

钉四条:
  ① 表格形状 = columns:[{key,label}] + dict 行(上一轮就是形状漂了导致页面全是 [object Object]);
  ② 表头与格子里的机器词全部翻成人话(印 no_numbers / never 等于让人自己解码);
  ③ 「还没算出来」不许渲染成 0,「还差几张」要按四种情况分开说(下一步动作不同);
  ④ zh/th 两语齐,词表 key 集合一致。
"""

from __future__ import annotations

import unittest

from services.steward import copy, copy_artifacts, copy_period, registry, tools_period
from services.workorder import push_coverage

_LANGS = ("zh", "th")


def _tax_data(**over):
    data = {
        "period": "2569-07",
        "client_count": 3,
        "ready": 2,
        "no_numbers": 1,
        "no_order": 0,
        "credit": 0,
        "totals": {
            "sales_amount": "2000000.00",
            "output_vat": "140000.00",
            "purchase_amount": "900000.00",
            "input_vat": "63000.00",
            "tax_due": "77000.00",
        },
        "rows": [
            {
                "client_id": 1,
                "client_name": "Sister Makeup",
                "state": tools_period.TAX_READY,
                "sales_amount": "1000000.00",
                "output_vat": "70000.00",
                "purchase_amount": "500000.00",
                "input_vat": "35000.00",
                "tax_due": "35000.00",
            },
            {
                "client_id": 2,
                "client_name": "62AHATAI",
                "state": tools_period.TAX_NO_NUMBERS,
                "sales_amount": "",
                "output_vat": "",
                "purchase_amount": "",
                "input_vat": "",
                "tax_due": "",
            },
        ],
        "truncated": False,
    }
    data.update(over)
    return data


def _invoice_data(**over):
    data = {
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "filter": tools_period.FILTER_ALL,
        "has_order": True,
        "work_order_id": "w1",
        "client_id": 1,
        "total": 4,
        "counts": {
            push_coverage.STATE_PUSHED: 1,
            push_coverage.STATE_FAILED: 1,
            push_coverage.STATE_IN_FLIGHT: 0,
            push_coverage.STATE_NEVER: 1,
            tools_period.INVOICE_PENDING_REVIEW: 1,
            tools_period.INVOICE_NO_NUMBER: 0,
        },
        "not_pushed": 3,
        "shown": 4,
        "rows": [
            {
                "invoice_no": "IV-1",
                "vendor": "7-11",
                "invoice_date": "2026-06-30",
                "amount": "107.00",
                "state": push_coverage.STATE_NEVER,
            }
        ],
        "truncated": False,
    }
    data.update(over)
    return data


class TaxMatrixCopyTests(unittest.TestCase):
    def test_reply_states_totals_and_pending_separately(self):
        said = copy.reply(registry.TAX_MATRIX, _tax_data(), "zh")
        self.assertIn("77000.00", said)
        self.assertIn("2/3", said)
        self.assertIn("还没算到税额 1 家", said)

    def test_credit_is_called_out(self):
        said = copy.reply(registry.TAX_MATRIX, _tax_data(credit=2), "zh")
        self.assertIn("留抵 2 家", said)

    def test_none_ready_does_not_print_zero_totals(self):
        """一家都没算出来时印「应交合计 ฿0.00」= 告诉老板这个月不用交钱。"""
        said = copy.reply(registry.TAX_MATRIX, _tax_data(ready=0, no_numbers=2, no_order=1), "zh")
        self.assertNotIn("฿0.00", said)
        self.assertIn("还没有一家算出税额", said)

    def test_empty_scope_speaks(self):
        said = copy.reply(registry.TAX_MATRIX, _tax_data(client_count=0, ready=0), "zh")
        self.assertTrue(said.strip())

    def test_truncation_says_totals_still_cover_everyone(self):
        said = copy.reply(registry.TAX_MATRIX, _tax_data(truncated=True), "zh")
        self.assertIn("合计是全部的", said)

    def test_artifacts_shape_and_translated_state(self):
        arts = copy.artifacts(registry.TAX_MATRIX, _tax_data(), "zh")
        table = [a for a in arts if a["kind"] == "table"][0]
        _assert_table(self, table)
        states = [r["state"] for r in table["rows"]]
        self.assertEqual(states, ["已算出", "还没算到"])
        self.assertEqual(table["rows"][1]["tax_due"], "")  # 空着,不是 0.00

    def test_artifacts_link_points_at_matrix_page(self):
        arts = copy.artifacts(registry.TAX_MATRIX, _tax_data(), "zh")
        self.assertEqual([a["href"] for a in arts if a["kind"] == "deeplink"], ["/ai#/"])

    def test_no_rows_no_table(self):
        arts = copy.artifacts(registry.TAX_MATRIX, _tax_data(rows=[]), "zh")
        self.assertEqual([a for a in arts if a["kind"] == "table"], [])


class PeriodInvoicesCopyTests(unittest.TestCase):
    def test_reply_breaks_down_the_not_pushed(self):
        said = copy.reply(registry.PERIOD_INVOICES, _invoice_data(), "zh")
        self.assertIn("已推进 Express 1 张", said)
        self.assertIn("还差 3 张", said)
        self.assertIn("推失败 1", said)
        self.assertIn("待判 1", said)
        self.assertNotIn("推送中 0", said)  # 零的桶不进句子(噪音)

    def test_all_pushed_says_so(self):
        counts = {s: 0 for s in tools_period.INVOICE_STATES}
        counts[push_coverage.STATE_PUSHED] = 4
        said = copy.reply(
            registry.PERIOD_INVOICES, _invoice_data(counts=counts, not_pushed=0), "zh"
        )
        self.assertIn("全部推进 Express 了", said)

    def test_no_order_and_no_invoice_are_different_sentences(self):
        no_order = copy.reply(registry.PERIOD_INVOICES, _invoice_data(has_order=False), "zh")
        empty = copy.reply(registry.PERIOD_INVOICES, _invoice_data(total=0, rows=[], shown=0), "zh")
        self.assertIn("还没开工单", no_order)
        self.assertNotEqual(no_order, empty)

    def test_filter_with_no_hits_says_which_filter(self):
        said = copy.reply(
            registry.PERIOD_INVOICES,
            _invoice_data(filter=tools_period.FILTER_NOT_PUSHED, shown=0, rows=[]),
            "zh",
        )
        self.assertIn("还没推进去的", said)

    def test_artifacts_shape_and_translated_state(self):
        arts = copy.artifacts(registry.PERIOD_INVOICES, _invoice_data(), "zh")
        table = [a for a in arts if a["kind"] == "table"][0]
        _assert_table(self, table)
        self.assertEqual(table["rows"][0]["state"], "还没推")

    def test_artifacts_link_points_at_the_client_work_order(self):
        arts = copy.artifacts(registry.PERIOD_INVOICES, _invoice_data(), "zh")
        hrefs = [a["href"] for a in arts if a["kind"] == "deeplink"]
        self.assertEqual(hrefs, ["/ai#/client/1/wo?period=2569-07"])


class VocabularyTests(unittest.TestCase):
    def test_unknown_future_words_are_not_dressed_up(self):
        for fn in (copy_period.tax_state, copy_period.invoice_state):
            self.assertEqual(fn("some_future_state", "zh"), "some_future_state")

    def test_every_vocabulary_entry_has_both_languages(self):
        for table in (copy_period._TAX_STATE, copy_period._INVOICE_STATE, copy_period.TITLES):
            for key, langs in table.items():
                self.assertEqual(set(langs), set(_LANGS), key)

    def test_every_invoice_state_has_a_word(self):
        """六态少翻一个,表格里就会冒出机器词。"""
        for state in tools_period.INVOICE_STATES:
            for lang in _LANGS:
                self.assertNotEqual(copy_period.invoice_state(state, lang), state, state)

    def test_every_tax_state_has_a_word(self):
        for state in (
            tools_period.TAX_READY,
            tools_period.TAX_NO_NUMBERS,
            tools_period.TAX_NO_ORDER,
        ):
            for lang in _LANGS:
                self.assertNotEqual(copy_period.tax_state(state, lang), state, state)

    def test_column_labels_exist_for_every_key_the_two_tools_emit(self):
        emitted = {
            "client_name",
            "sales_amount",
            "output_vat",
            "purchase_amount",
            "input_vat",
            "tax_due",
            "state",
            "invoice_no",
            "vendor",
            "invoice_date",
            "amount",
        }
        for key in emitted:
            for lang in _LANGS:
                self.assertTrue(
                    copy_artifacts._COLUMN_LABEL.get(key, {}).get(lang), f"{key}/{lang}"
                )

    def test_both_tools_reply_in_thai_too(self):
        for tool, data in (
            (registry.TAX_MATRIX, _tax_data()),
            (registry.PERIOD_INVOICES, _invoice_data()),
        ):
            self.assertTrue(copy.reply(tool, data, "th").strip(), tool)
            self.assertTrue(copy.tool_title(tool, "th"), tool)


def _assert_table(case: unittest.TestCase, art: dict) -> None:
    """B2 的形状契约:columns=[{key,label}] + 行是 dict 且按 key 取得到值。"""
    case.assertEqual(art["kind"], "table")
    case.assertTrue(art["label"])
    case.assertTrue(art["columns"])
    for col in art["columns"]:
        case.assertEqual(set(col), {"key", "label"})
        case.assertTrue(col["label"])
    keys = [c["key"] for c in art["columns"]]
    for row in art["rows"]:
        case.assertIsInstance(row, dict)
        case.assertEqual(set(row), set(keys))
        for value in row.values():
            case.assertNotIsInstance(value, (dict, list))


if __name__ == "__main__":
    unittest.main()
