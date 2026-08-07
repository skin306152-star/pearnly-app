# -*- coding: utf-8 -*-
"""管家商品收发存查询 stock_card_lookup(services/steward/tools_stockcard.py + copy_stockcard)。

数据源必须是 services.stockcard.report(事务所记账台账),绝不是 services.inventory
(POS 商户库存·两回事)—— 本文件的桩全部打在 report.summary/report.card 上,任何一条测试
如果换成打 services.inventory 就说明实现走错了数据源,应当红。

断言分两类:
  ① 逻辑(候选定位 / 汇总口径 / 负库存原样负数展示 / 期间→日期换算);
  ② 文案渲染(zh + th 都要有字、负库存的成因提示句、报表页指路句)。
零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.steward import copy, registry, tool_scope, tools_stockcard
from services.steward.registry import ToolContext
from services.stockcard import report as report_svc

_LANGS = ("zh", "th")
_CLIENTS = [
    {"id": 1, "name": "Sister Makeup", "tax_id": "0105500001234"},
    {"id": 2, "name": "62AHATAI", "tax_id": "0105500009999"},
]

_SHAMPOO = {
    "key": "p:abc",
    "product_id": "abc",
    "name": "Shampoo",
    "unit": "ขวด",
    "opening_qty": "10",
    "in_qty": "5",
    "out_qty": "20",
    "bal_qty": "-5",
    "bal_unit_cost": "50.00",
    "bal_value": "-250.00",
    "negative": True,
    "matched": True,
}
_SOAP = {
    "key": "n:soap",
    "product_id": None,
    "name": "Soap",
    "unit": None,
    "opening_qty": "0",
    "in_qty": "3",
    "out_qty": "1",
    "bal_qty": "2",
    "bal_unit_cost": "20.00",
    "bal_value": "40.00",
    "negative": False,
    "matched": False,
}
_SUMMARY = {"products": [_SHAMPOO, _SOAP], "excluded_count": 2}

_CARD = {
    "product": {"key": "p:abc", "product_id": "abc", "name": "Shampoo", "unit": "ขวด"},
    "rows": [
        {
            "date": "2026-07-01",
            "doc_no": "",
            "kind": "open",
            "desc": "",
            "qty": "10",
            "unit_price": None,
            "amount": None,
            "bal_qty": "10",
            "bal_unit_cost": "50.00",
            "bal_value": "500.00",
        },
    ],
    "totals": {
        "in_qty": "5",
        "in_amount": "250.00",
        "out_qty": "20",
        "out_amount": "1000.00",
        "bal_qty": "-5",
        "bal_unit_cost": "50.00",
        "bal_value": "-250.00",
    },
}


def _ctx(allowed=None):
    return ToolContext(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        allowed_client_ids=allowed,
        today=date(2026, 7, 10),
    )


class _CurCM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class _LookupCase(unittest.TestCase):
    def _run(self, args=None, summary=None, card=None, ctx=None):
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(report_svc, "load_context", return_value=("data-stub", {})),
            mock.patch.object(
                report_svc, "summary", return_value=summary if summary is not None else _SUMMARY
            ) as sm,
            mock.patch.object(
                report_svc, "card", return_value=card if card is not None else _CARD
            ) as cd,
        ):
            res = tools_stockcard.stock_card_lookup(
                ctx or _ctx(),
                {"client_name": "makeup", "period": "2569-07", **(args or {})},
            )
        return res, sm, cd


class SummaryViewTests(_LookupCase):
    def test_counts_products_negative_and_unmatched(self):
        res, sm, _cd = self._run()
        self.assertTrue(res.ok)
        self.assertEqual(res.data["product_count"], 2)
        self.assertEqual(res.data["negative_count"], 1)
        self.assertEqual(res.data["unmatched_count"], 1)
        self.assertEqual(res.data["bal_value_total"], "-210.00")  # -250.00 + 40.00,decimal 相加
        self.assertEqual(sm.call_args.kwargs["workspace_client_id"], 1)
        self.assertEqual(sm.call_args.kwargs["date_from"], date(2026, 7, 1))
        self.assertEqual(sm.call_args.kwargs["date_to"], date(2026, 7, 31))

    def test_negative_row_keeps_the_sign_not_absolute_value(self):
        """负库存必须原样负数展示 —— 拿 abs() 冒充"缺口大小"是篡改事实。"""
        res, _sm, _cd = self._run()
        self.assertEqual(res.data["negative_rows"][0]["bal_qty"], "-5")

    def test_no_period_defaults_to_current_month(self):
        with mock.patch.object(tool_scope, "period_or_current", return_value="2569-08"):
            res, sm, _cd = self._run(args={"period": None})
        self.assertEqual(res.data["period"], "2569-08")
        self.assertEqual(sm.call_args.kwargs["date_from"], date(2026, 8, 1))

    def test_empty_products_is_its_own_answer(self):
        res, _sm, _cd = self._run(summary={"products": [], "excluded_count": 0})
        self.assertEqual(res.data["product_count"], 0)

    def test_unknown_client_refuses_instead_of_guessing(self):
        res, _sm, _cd = self._run(args={"client_name": "nobody there", "period": "2569-07"})
        # client_name 由测试 args 覆盖,但候选池仍是 _CLIENTS —— 查无
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)


class KeywordLookupTests(_LookupCase):
    def test_unique_hit_calls_card_and_returns_product_summary(self):
        res, sm, cd = self._run(args={"keyword": "Shampoo"})
        self.assertTrue(res.ok)
        self.assertEqual(res.data["product"]["name"], "Shampoo")
        self.assertEqual(res.data["opening_qty"], "10")  # rows[0] 的合成"期初"行
        self.assertEqual(res.data["totals"]["bal_qty"], "-5")
        self.assertEqual(cd.call_args.kwargs["key"], "p:abc")
        # summary/card 共用同一次 load_context 装载,不重复全表扫描。
        self.assertIs(sm.call_args.kwargs["context"], cd.call_args.kwargs["context"])

    def test_no_match_asks_instead_of_guessing(self):
        res, _sm, _cd = self._run(args={"keyword": "不存在的商品"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_stockcard.ERR_PRODUCT_NOT_FOUND)

    def test_ambiguous_keyword_returns_candidates(self):
        """ "o" 同时命中 Shampoo 与 Soap(宽松子串匹配)—— 不猜,退回候选。"""
        res, _sm, cd = self._run(args={"keyword": "o"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_stockcard.ERR_PRODUCT_AMBIGUOUS)
        self.assertEqual(len(res.data["candidates"]), 2)
        cd.assert_not_called()  # 命中多个之前不该已经在调 card


class CopyTests(unittest.TestCase):
    _SUMMARY_DATA = {
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "product_count": 2,
        "negative_count": 1,
        "unmatched_count": 1,
        "bal_value_total": "-210.00",
        "excluded_count": 2,
        "negative_rows": [{"name": "Shampoo", "bal_qty": "-5"}],
        "sample_rows": [],
    }
    _PRODUCT_DATA = {
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "keyword": "Shampoo",
        "product": {"key": "p:abc", "product_id": "abc", "name": "Shampoo", "unit": "ขวด"},
        "opening_qty": "10",
        "totals": {
            "in_qty": "5",
            "in_amount": "250.00",
            "out_qty": "20",
            "out_amount": "1000.00",
            "bal_qty": "-5",
            "bal_unit_cost": "50.00",
            "bal_value": "-250.00",
        },
    }

    def test_summary_reply_names_negative_products_with_balance(self):
        for lang in _LANGS:
            text = copy.reply(registry.STOCK_CARD_LOOKUP, self._SUMMARY_DATA, lang)
            self.assertIn("Shampoo", text)
            self.assertIn("-5", text)  # 负数原样,不是绝对值

    def test_summary_reply_points_to_the_report_page(self):
        zh = copy.reply(registry.STOCK_CARD_LOOKUP, self._SUMMARY_DATA, "zh")
        th = copy.reply(registry.STOCK_CARD_LOOKUP, self._SUMMARY_DATA, "th")
        self.assertIn("收发存报表", zh)
        self.assertIn("สต็อคการ์ด", th)

    def test_summary_reply_is_empty_case_when_no_products(self):
        data = {**self._SUMMARY_DATA, "product_count": 0}
        for lang in _LANGS:
            text = copy.reply(registry.STOCK_CARD_LOOKUP, data, lang)
            self.assertTrue(text)

    def test_product_reply_carries_opening_in_out_balance(self):
        text = copy.reply(registry.STOCK_CARD_LOOKUP, self._PRODUCT_DATA, "zh")
        self.assertIn("Shampoo", text)
        self.assertIn("10", text)  # 期初
        self.assertIn("-5", text)  # 结存(负数原样)

    def test_product_reply_flags_negative_with_the_cause_sentence(self):
        for lang in _LANGS:
            text = copy.reply(registry.STOCK_CARD_LOOKUP, self._PRODUCT_DATA, lang)
            self.assertIn("บิลซื้ออาจไม่ครบ" if lang == "th" else "采购票可能没送齐", text)

    def test_product_reply_omits_negative_note_when_balance_is_not_negative(self):
        data = {**self._PRODUCT_DATA, "totals": {**self._PRODUCT_DATA["totals"], "bal_qty": "5"}}
        text = copy.reply(registry.STOCK_CARD_LOOKUP, data, "zh")
        self.assertNotIn("负库存", text)

    def test_error_not_found_names_the_keyword(self):
        data = {"client_name": "Sister Makeup", "period": "2569-07", "keyword": "洗发水"}
        for lang in _LANGS:
            text = copy.error(tools_stockcard.ERR_PRODUCT_NOT_FOUND, data, lang)
            self.assertIn("洗发水", text)

    def test_error_ambiguous_lists_candidates(self):
        data = {
            "keyword": "o",
            "total": 2,
            "candidates": [
                {"key": "p:abc", "name": "Shampoo", "bal_qty": "-5"},
                {"key": "n:soap", "name": "Soap", "bal_qty": "2"},
            ],
        }
        for lang in _LANGS:
            text = copy.error(tools_stockcard.ERR_PRODUCT_AMBIGUOUS, data, lang)
            self.assertIn("Shampoo", text)
            self.assertIn("Soap", text)

    def test_title_exists_in_both_languages(self):
        for lang in _LANGS:
            self.assertTrue(copy.tool_title(registry.STOCK_CARD_LOOKUP, lang))


if __name__ == "__main__":
    unittest.main()
