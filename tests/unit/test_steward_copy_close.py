# -*- coding: utf-8 -*-
"""月结产线四问 + 单票体检的文案与产物(copy_close / copy_artifacts · B4)。

三类断言:
  ① 答复的数字全部来自 data(模板只填空);「没有」与「零」必须说成两句话;
  ② 产物形状照 B2 定下的契约 columns=[{key,label}] + 行是 dict —— 上一轮就是形状漂了,
     页面渲染出满屏 [object Object];
  ③ 深链只指真实存在的 /ai 路由,机器词一律翻成人话再上表。
zh/th 两语齐,新工具一个不落。
"""

from __future__ import annotations

import unittest

from services.steward import copy, copy_artifacts, copy_close, registry

_LANGS = ("zh", "th")
_NEW_TOOLS = (
    registry.DUE_SOON,
    registry.REVIEW_QUEUE,
    registry.TAX_NUMBERS,
    registry.BANK_RECON_STATUS,
    registry.INVOICE_DETAIL,
)

# /ai SPA 真实存在的路由前缀(static/ai/ai-router.js 的 build*Hash)。深链落空是老坑。
_REAL_ROUTES = ("/ai#/", "/ai#/board", "/ai#/client/")


class TitleTests(unittest.TestCase):
    def test_every_new_tool_has_a_title_in_both_languages(self):
        for tool in _NEW_TOOLS:
            for lang in _LANGS:
                title = copy.tool_title(tool, lang)
                self.assertTrue(title, f"{tool}/{lang}")
                self.assertNotEqual(title, tool, f"{tool}/{lang} 还是机器名")

    def test_out_of_scope_blurb_advertises_the_new_capabilities(self):
        """能力清单说少了 = 产品在自谦到撒谎的地步,会计不会去问它做得到的事。"""
        self.assertIn("到期", copy.out_of_scope("zh"))
        self.assertIn("银行对账", copy.out_of_scope("zh"))
        self.assertTrue(copy.out_of_scope("th"))


class DueSoonCopyTests(unittest.TestCase):
    _DATA = {
        "period": "2569-07",
        "window_days": 7,
        "total": 4,
        "overdue": 1,
        "due_soon": 2,
        "no_due_date": 0,
        "rows": [
            {
                "client_name": "62AHATAI",
                "obligation_code": "pp30",
                "due": "2026-07-07",
                "days_left": -3,
                "badge": "missing_materials",
            }
        ],
    }

    def test_numbers_come_from_data(self):
        text = copy.reply(registry.DUE_SOON, self._DATA, "zh")
        for token in ("2569-07", "4", "1", "2", "62AHATAI", "pp30"):
            self.assertIn(token, text)

    def test_overdue_is_spelled_out_not_a_negative_number(self):
        text = copy.reply(registry.DUE_SOON, self._DATA, "zh")
        self.assertIn("已逾期 3 天", text)
        self.assertNotIn("-3", text)

    def test_nothing_owed_is_its_own_sentence(self):
        data = {**self._DATA, "total": 0, "overdue": 0, "due_soon": 0, "rows": []}
        for lang in _LANGS:
            self.assertTrue(copy.reply(registry.DUE_SOON, data, lang))
        self.assertNotIn("最近一项", copy.reply(registry.DUE_SOON, data, "zh"))

    def test_days_left_none_is_not_rendered_as_zero(self):
        self.assertNotIn("0", copy_close.days_left(None, "zh"))
        self.assertIn("就是今天", copy_close.days_left(0, "zh"))

    def test_table_shape_and_humanised_cells(self):
        arts = copy.artifacts(registry.DUE_SOON, self._DATA, "zh")
        link, table = arts[0], arts[1]
        self.assertEqual(link["kind"], "deeplink")
        self.assertIn(link["href"], _REAL_ROUTES)
        _assert_table(self, table)
        row = table["rows"][0]
        self.assertEqual(row["days_left"], "已逾期 3 天")
        self.assertEqual(row["badge"], "缺料")


class ReviewQueueCopyTests(unittest.TestCase):
    _DATA = {
        "period": "2569-07",
        "severity": "crit",
        "client_name": "",
        "client_count": 3,
        "order_count": 5,
        "flagged_count": 11,
        "rows": [
            {
                "client_name": "Sister Makeup",
                "period": "2569-07",
                "status": "stuck",
                "flagged": 3,
                "severity": "crit",
                "due": "2026-07-15",
            }
        ],
    }

    def test_counts_and_filter_are_stated(self):
        text = copy.reply(registry.REVIEW_QUEUE, self._DATA, "zh")
        self.assertIn("5", text)
        self.assertIn("3", text)
        self.assertIn("11", text)
        self.assertIn("严重", text)

    def test_empty_queue_says_so_in_both_languages(self):
        data = {**self._DATA, "order_count": 0, "client_count": 0, "flagged_count": 0, "rows": []}
        for lang in _LANGS:
            self.assertTrue(copy.reply(registry.REVIEW_QUEUE, data, lang))

    def test_deeplink_points_at_the_board_not_an_invented_route(self):
        link = copy.artifacts(registry.REVIEW_QUEUE, self._DATA, "zh")[0]
        self.assertEqual(link["href"], "/ai#/board")

    def test_machine_words_are_translated_in_the_table(self):
        table = copy.artifacts(registry.REVIEW_QUEUE, self._DATA, "zh")[1]
        _assert_table(self, table)
        self.assertEqual(table["rows"][0]["status"], "卡住等人")
        self.assertEqual(table["rows"][0]["severity"], "严重")


class TaxNumbersCopyTests(unittest.TestCase):
    _DATA = {
        "client_id": 1,
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "has_order": True,
        "has_numbers": True,
        "sales_amount": "1000000.00",
        "output_vat": "70000.00",
        "purchase_amount": "400000.00",
        "input_vat": "28000.00",
        "tax_due": "42000.00",
    }

    def test_all_five_numbers_are_reported(self):
        text = copy.reply(registry.TAX_NUMBERS, self._DATA, "zh")
        for token in ("1000000.00", "70000.00", "400000.00", "28000.00", "42000.00"):
            self.assertIn(token, text)

    def test_not_computed_yet_is_not_rendered_as_zero_due(self):
        data = {**self._DATA, "has_numbers": False, "status": "running", "current_step": "classify"}
        text = copy.reply(registry.TAX_NUMBERS, data, "zh")
        self.assertNotIn("应交 ฿", text)
        self.assertIn("执行中", text)

    def test_no_order_is_its_own_sentence(self):
        data = {**self._DATA, "has_order": False, "has_numbers": False}
        for lang in _LANGS:
            self.assertTrue(copy.reply(registry.TAX_NUMBERS, data, lang))

    def test_deeplink_targets_this_client_this_period(self):
        link = copy.artifacts(registry.TAX_NUMBERS, self._DATA, "zh")[0]
        self.assertEqual(link["href"], "/ai#/client/1/wo?period=2569-07")

    def test_no_deeplink_without_a_resolved_client(self):
        self.assertEqual(copy.artifacts(registry.TAX_NUMBERS, {"period": "2569-07"}, "zh"), [])


class BankReconCopyTests(unittest.TestCase):
    _DATA = {
        "client_id": 1,
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "has_order": True,
        "has_recon": True,
        "auto_matched": 12,
        "review": 2,
        "missing_invoice": 3,
        "unmatched_invoice": 1,
        "net": "3300.00",
        "rows": [{"tx_date": "2026-06-11", "amount": "4500.00", "description": "PAYMENT 7-11"}],
    }

    def test_four_lists_and_net_difference_are_reported(self):
        text = copy.reply(registry.BANK_RECON_STATUS, self._DATA, "zh")
        for token in ("12", "2", "3", "1", "3300.00"):
            self.assertIn(token, text)

    def test_no_recon_is_not_rendered_as_balanced(self):
        data = {**self._DATA, "has_recon": False}
        text = copy.reply(registry.BANK_RECON_STATUS, data, "zh")
        self.assertNotIn("3300.00", text)
        self.assertNotIn("对上", text)
        self.assertTrue(copy.reply(registry.BANK_RECON_STATUS, data, "th"))

    def test_only_the_missing_invoice_list_becomes_a_table(self):
        arts = copy.artifacts(registry.BANK_RECON_STATUS, self._DATA, "zh")
        table = arts[1]
        _assert_table(self, table)
        self.assertEqual([c["key"] for c in table["columns"]], ["tx_date", "amount", "description"])


class InvoiceDetailCopyTests(unittest.TestCase):
    _DATA = {
        "history_id": "h1",
        "invoice_no": "RR581231-002",
        "seller_name": "7-11",
        "invoice_date": "2026-06-30",
        "total_amount": "401621.50",
        "posting_kind": "stock",
        "push_count": 0,
        "push_status": "",
        "push_rows": [],
    }

    def test_face_fields_and_never_pushed(self):
        text = copy.reply(registry.INVOICE_DETAIL, self._DATA, "zh")
        self.assertIn("RR581231-002", text)
        self.assertIn("401621.50", text)
        self.assertIn("库存", text)
        self.assertIn("还没推过", text)

    def test_missing_posting_kind_says_reupload_not_retry(self):
        """重试带不上过账去向(产品里补不了)—— 不说清楚会计会一直点重试。"""
        data = {**self._DATA, "posting_kind": ""}
        text = copy.reply(registry.INVOICE_DETAIL, data, "zh")
        self.assertIn("没声明", text)
        self.assertIn("重新上传", text)

    def test_push_failure_points_at_the_push_log(self):
        data = {
            **self._DATA,
            "push_count": 2,
            "push_status": "failed",
            "push_error_code": "ERR_NO_ACC",
        }
        text = copy.reply(registry.INVOICE_DETAIL, data, "zh")
        self.assertIn("ERR_NO_ACC", text)
        self.assertIn("推送日志", text)

    def test_push_success_is_stated_once(self):
        data = {**self._DATA, "push_count": 1, "push_status": "success", "push_at": "2026-07-09"}
        self.assertIn("2026-07-09", copy.reply(registry.INVOICE_DETAIL, data, "zh"))

    def test_attempts_table_shape(self):
        data = {
            **self._DATA,
            "push_count": 1,
            "push_status": "failed",
            "push_rows": [
                {
                    "created_at": "2026-07-09",
                    "status": "failed",
                    "error_code": "ERR_NO_ACC",
                    "category": "account_missing",
                }
            ],
        }
        _assert_table(self, copy.artifacts(registry.INVOICE_DETAIL, data, "zh")[0])


class VocabularyTests(unittest.TestCase):
    def test_unknown_future_words_are_not_dressed_up(self):
        for fn in (copy_close.order_status, copy_close.badge, copy_close.severity):
            self.assertEqual(fn("some_future_state", "zh"), "some_future_state")

    def test_every_vocabulary_entry_has_both_languages(self):
        tables = (copy_close._ORDER_STATUS, copy_close._BADGE, copy_close._SEVERITY)
        for table in tables:
            for key, langs in table.items():
                self.assertEqual(set(langs), set(_LANGS), key)

    def test_column_labels_exist_for_every_key_the_tools_emit(self):
        """表头缺 label 会退回机器 key —— 表格上印 days_left 等于没翻译。"""
        emitted = {
            "client_name",
            "obligation_code",
            "due",
            "days_left",
            "badge",
            "period",
            "status",
            "flagged",
            "severity",
            "tx_date",
            "amount",
            "description",
            "created_at",
            "error_code",
            "category",
        }
        for key in emitted:
            for lang in _LANGS:
                self.assertTrue(
                    copy_artifacts._COLUMN_LABEL.get(key, {}).get(lang), f"{key}/{lang}"
                )


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
