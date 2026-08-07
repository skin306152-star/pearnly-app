# -*- coding: utf-8 -*-
"""管家签批闸 close_readiness(services/steward/tools_signoff.py + copy_brief · B5)。

这个工具的答案会被拿来决定要不要签字担责,所以每条断言都对着一条判据:
  ① 判据逐项来自 order_detail 的既有投影,不是模型的综合评价(用例桩 order_detail 本身);
  ② 「不知道」是第三态:没收到银行流水不该被判成"没过",也绝不当成"已对平";
  ③ 签过之后引擎重跑(stale)当没签,答复必须说要重签 —— 那次签名担保的不是眼下这份账;
  ④ 没开工单 ≠ 五项全不合格,得是另一句话;
  ⑤ 账套作用域与客户名接地照旧(挂错账套是红线)。
零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.steward import copy, copy_artifacts, copy_brief, registry, tool_scope, tools_signoff
from services.steward.registry import ToolContext
from services.stockcard import report as report_svc
from services.workorder import api as wo_api

_LANGS = ("zh", "th")
_CLIENTS = [
    {"id": 1, "name": "Sister Makeup", "tax_id": "0105500001234"},
    {"id": 2, "name": "62AHATAI", "tax_id": "0105500009999"},
]
# 六项里第五项(负库存)默认查得到、没有负结存 —— 与其余四项互不相关的用例不必逐个再写一份桩。
_NO_NEGATIVE_STOCK = {"products": [], "excluded_count": 0}


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


def _detail(**over):
    """一张五项全过、还没人签的工单详情(各用例只改自己关心的那一项)。"""
    detail = {
        "id": "w1",
        "status": "review",
        "current_step": "package",
        "numbers": {"tax_due": "42000.00"},
        "bank_recon": {"missing_invoice_count": 0, "review_count": 0},
        "flagged": [],
        "deliverables": [{"kind": "pp30_draft", "numbers": {}}],
        "signoff": None,
    }
    detail.update(over)
    return detail


class _SignoffCase(unittest.TestCase):
    def _run(self, detail, args=None, ctx=None, orders=("w1",), stock_summary=None):
        listing = {"orders": [{"id": o} for o in orders], "count": len(orders)}
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(wo_api, "list_orders", return_value=listing) as lst,
            mock.patch.object(wo_api, "order_detail", return_value=detail) as det,
            mock.patch.object(
                report_svc,
                "summary",
                return_value=stock_summary if stock_summary is not None else _NO_NEGATIVE_STOCK,
            ) as stk,
        ):
            res = tools_signoff.close_readiness(
                ctx or _ctx(), {"client_name": "makeup", "period": "2569-07", **(args or {})}
            )
        self.stock_mock = stk
        return res, lst, det

    def _state(self, res, check):
        return next(c for c in res.data["checks"] if c["check"] == check)


class VerdictTests(_SignoffCase):
    def test_all_prerequisites_pass_reads_ready(self):
        res, lst, det = self._run(_detail())
        self.assertTrue(res.ok)
        self.assertEqual(lst.call_args.kwargs["workspace_client_id"], 1)
        self.assertEqual(det.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(res.data["verdict"], tools_signoff.VERDICT_READY)
        self.assertEqual(res.data["blocking"], 0)
        self.assertEqual(len(res.data["checks"]), 6)

    def test_signed_is_reported_before_anything_else(self):
        res, _lst, _det = self._run(
            _detail(signoff={"actor": "user:kanya", "at": "2026-07-09T10:00:00", "stale": False})
        )
        self.assertEqual(res.data["verdict"], tools_signoff.VERDICT_SIGNED)
        self.assertEqual(res.data["signoff_actor"], "user:kanya")
        self.assertEqual(self._state(res, tools_signoff.CHECK_SIGNOFF)["state"], "ok")

    def test_stale_signoff_counts_as_unsigned_and_asks_for_a_resign(self):
        res, _lst, _det = self._run(
            _detail(signoff={"actor": "user:kanya", "at": "2026-07-09T10:00:00", "stale": True})
        )
        self.assertEqual(res.data["verdict"], tools_signoff.VERDICT_RESIGN)
        row = self._state(res, tools_signoff.CHECK_SIGNOFF)
        self.assertEqual(row["state"], tools_signoff.STATE_BLOCKED)
        self.assertEqual(row["reason"], "stale")

    def test_no_order_is_its_own_answer_not_five_failures(self):
        res, _lst, det = self._run(None, orders=())
        self.assertTrue(res.ok)
        self.assertFalse(res.data["has_order"])
        self.assertEqual(res.data["verdict"], tools_signoff.VERDICT_NOT_STARTED)
        self.assertEqual(res.data["checks"], [])
        det.assert_not_called()

    def test_unknown_client_refuses_instead_of_guessing(self):
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
        ):
            res = tools_signoff.close_readiness(_ctx(), {"client_name": "nobody"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)

    def test_client_roster_is_narrowed_to_the_assigned_scope(self):
        """被分派成员在这条路上也只解析得到分到的账套(名录本身就是收窄过的)。"""
        from services.workspace import store as ws_store

        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(ws_store, "list_workspace_clients", return_value=[]) as roster,
        ):
            res = tools_signoff.close_readiness(
                _ctx(allowed=frozenset({7})), {"client_name": "makeup"}
            )
        self.assertEqual(roster.call_args.kwargs["restrict_ids"], [7])
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)


class CheckTests(_SignoffCase):
    def test_numbers_not_computed_blocks_and_is_not_read_as_zero_due(self):
        res, _lst, _det = self._run(_detail(numbers={}))
        row = self._state(res, tools_signoff.CHECK_NUMBERS)
        self.assertEqual(row["state"], tools_signoff.STATE_BLOCKED)
        self.assertEqual(row["reason"], "not_computed")
        self.assertEqual(res.data["verdict"], tools_signoff.VERDICT_BLOCKED)

    def test_zero_tax_due_still_counts_as_computed(self):
        """应交 0 是算过的结果,不是"没算" —— 拿它拦签批就是把正确的账判成不合格。"""
        res, _lst, _det = self._run(_detail(numbers={"tax_due": "0.00"}))
        self.assertEqual(self._state(res, tools_signoff.CHECK_NUMBERS)["state"], "ok")

    def test_outstanding_bank_items_block_with_a_count(self):
        res, _lst, _det = self._run(
            _detail(bank_recon={"missing_invoice_count": 2, "review_count": 1})
        )
        row = self._state(res, tools_signoff.CHECK_BANK)
        self.assertEqual(row["reason"], "outstanding")
        self.assertEqual(row["n"], 3)

    def test_invoice_without_bank_movement_does_not_block(self):
        """有票无流水是赊销常态,拿它拦签批会天天误报。"""
        res, _lst, _det = self._run(
            _detail(
                bank_recon={
                    "missing_invoice_count": 0,
                    "review_count": 0,
                    "unmatched_invoice_count": 9,
                }
            )
        )
        self.assertEqual(self._state(res, tools_signoff.CHECK_BANK)["state"], "ok")

    def test_no_bank_recon_is_unknown_not_a_failure_and_not_balanced(self):
        res, _lst, _det = self._run(_detail(bank_recon=None))
        row = self._state(res, tools_signoff.CHECK_BANK)
        self.assertEqual(row["state"], tools_signoff.STATE_UNKNOWN)
        self.assertEqual(row["reason"], "no_recon")
        # 不知道也不能签(不知道 ≠ 过),但答复要说的是"不知道"而不是"没过"
        self.assertEqual(res.data["verdict"], tools_signoff.VERDICT_BLOCKED)

    def test_pending_flagged_items_block_with_a_count(self):
        res, _lst, _det = self._run(_detail(flagged=[{"id": "a"}, {"id": "b"}]))
        row = self._state(res, tools_signoff.CHECK_FLAGGED)
        self.assertEqual(row["reason"], "pending")
        self.assertEqual(row["n"], 2)

    def test_no_deliverables_means_the_package_step_has_not_run(self):
        res, _lst, _det = self._run(_detail(deliverables=[]))
        self.assertEqual(
            self._state(res, tools_signoff.CHECK_DELIVERABLES)["reason"], "not_packaged"
        )

    def test_blocking_counts_only_the_four_prerequisites(self):
        """签批态本身不算前置(它是结果)——否则每张没签的单都会多算一项。"""
        res, _lst, _det = self._run(_detail())
        self.assertEqual(res.data["blocking"], 0)
        self.assertEqual(self._state(res, tools_signoff.CHECK_SIGNOFF)["state"], "blocked")


class NegativeStockCheckTests(_SignoffCase):
    """第六项(提示不拦截):负库存查得到就如实说,但绝不进签批前置(见模块顶注)。"""

    def test_negative_products_warn_without_blocking(self):
        res, _lst, _det = self._run(
            _detail(),
            stock_summary={
                "products": [
                    {"name": "แชมพู", "negative": True},
                    {"name": "สบู่", "negative": True},
                    {"name": "ผ้าเช็ดตัว", "negative": False},
                ],
                "excluded_count": 0,
            },
        )
        row = self._state(res, tools_signoff.CHECK_NEGATIVE_STOCK)
        self.assertEqual(row["state"], tools_signoff.STATE_WARN)
        self.assertEqual(row["n"], 2)
        # 提示项不进前置:四项都过时仍然 ready、blocking 仍然 0。
        self.assertEqual(res.data["verdict"], tools_signoff.VERDICT_READY)
        self.assertEqual(res.data["blocking"], 0)

    def test_zero_negative_products_reads_ok(self):
        res, _lst, _det = self._run(_detail())
        row = self._state(res, tools_signoff.CHECK_NEGATIVE_STOCK)
        self.assertEqual(row["state"], tools_signoff.STATE_OK)
        self.assertEqual(row["reason"], "no_negative_stock")

    def test_queries_the_same_client_and_period_as_the_signoff_call(self):
        self._run(_detail())
        self.assertEqual(self.stock_mock.call_args.kwargs["workspace_client_id"], 1)
        self.assertEqual(self.stock_mock.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(self.stock_mock.call_args.kwargs["date_from"].isoformat(), "2026-07-01")
        self.assertEqual(self.stock_mock.call_args.kwargs["date_to"].isoformat(), "2026-07-31")

    def test_query_failure_reads_unknown_and_does_not_crash_the_other_four_checks(self):
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(
                wo_api, "list_orders", return_value={"orders": [{"id": "w1"}], "count": 1}
            ),
            mock.patch.object(wo_api, "order_detail", return_value=_detail()),
            mock.patch.object(report_svc, "summary", side_effect=RuntimeError("stock db down")),
        ):
            res = tools_signoff.close_readiness(
                _ctx(), {"client_name": "makeup", "period": "2569-07"}
            )
        self.assertTrue(res.ok)  # 库存查询挂了不该把整个签批闸判成失败
        row = self._state(res, tools_signoff.CHECK_NEGATIVE_STOCK)
        self.assertEqual(row["state"], tools_signoff.STATE_UNKNOWN)
        # 其余四项照常算,没被这一项的异常拖垮。
        self.assertEqual(self._state(res, tools_signoff.CHECK_NUMBERS)["state"], "ok")
        self.assertEqual(res.data["verdict"], tools_signoff.VERDICT_READY)

    def test_blocked_reply_keeps_the_count_and_the_item_list_in_sync(self):
        """负库存 warn + 一项真前置(银行)没过:「差 N 项」的 N 与列出的理由必须逐一对应,
        负库存那句不许混进"没过"的清单里(它压根不是前置)。"""
        res, _lst, _det = self._run(
            _detail(bank_recon={"missing_invoice_count": 3, "review_count": 0}),
            stock_summary={"products": [{"name": "แชมพู", "negative": True}], "excluded_count": 0},
        )
        self.assertEqual(res.data["blocking"], 1)
        text = copy.reply(registry.CLOSE_READINESS, res.data, "zh")
        self.assertIn("差 1 项", text)
        self.assertIn("还有 3 笔缺票或待人审", text)
        self.assertNotIn("负结存", text)  # 提示项的理由不出现在"差 N 项"清单里


class CopyTests(unittest.TestCase):
    _DATA = {
        "client_id": 1,
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "has_order": True,
        "work_order_id": "w1",
        "status": "review",
        "verdict": "blocked",
        "blocking": 2,
        "signoff_actor": "",
        "signoff_at": "",
        "checks": [
            {"check": "numbers", "state": "ok", "reason": "computed", "n": None},
            {"check": "bank_recon", "state": "blocked", "reason": "outstanding", "n": 3},
            {"check": "flagged", "state": "ok", "reason": "clear", "n": None},
            {"check": "deliverables", "state": "blocked", "reason": "not_packaged", "n": None},
            {"check": "signoff", "state": "blocked", "reason": "unsigned", "n": None},
        ],
    }

    def test_blocked_reply_names_every_missing_item(self):
        text = copy.reply(registry.CLOSE_READINESS, self._DATA, "zh")
        self.assertIn("还不能签", text)
        self.assertIn("2", text)
        self.assertIn("还有 3 笔缺票或待人审", text)
        self.assertIn("交付包还没出", text)

    def test_ready_signed_and_resign_each_get_their_own_sentence(self):
        seen = set()
        for verdict in ("ready", "signed", "resign_needed", "not_started"):
            data = {**self._DATA, "verdict": verdict, "signoff_actor": "user:kanya"}
            for lang in _LANGS:
                text = copy.reply(registry.CLOSE_READINESS, data, lang)
                self.assertTrue(text, f"{verdict}/{lang}")
                seen.add(text)
        self.assertEqual(len(seen), 8)  # 四种结论 × 两语,没有一句复用别的

    def test_unknown_state_is_not_worded_as_failed(self):
        self.assertNotEqual(copy_brief.state("unknown", "zh"), copy_brief.state("blocked", "zh"))

    def test_table_shape_and_humanised_cells(self):
        arts = copy.artifacts(registry.CLOSE_READINESS, self._DATA, "zh")
        link, table = arts[0], arts[1]
        self.assertEqual(link["kind"], "deeplink")
        self.assertTrue(link["href"].startswith("/ai#/client/1/wo"))
        _assert_table(self, table)
        self.assertEqual(table["rows"][1]["check"], "银行对账")
        self.assertEqual(table["rows"][1]["result"], "没过")
        self.assertEqual(table["rows"][1]["reason"], "还有 3 笔缺票或待人审")

    def test_no_order_gives_no_table(self):
        data = {**self._DATA, "has_order": False, "checks": [], "verdict": "not_started"}
        self.assertEqual(
            [a["kind"] for a in copy.artifacts(registry.CLOSE_READINESS, data, "zh")], ["deeplink"]
        )

    def test_column_labels_exist_in_both_languages(self):
        for key in ("check", "result", "reason"):
            for lang in _LANGS:
                self.assertTrue(
                    copy_artifacts._COLUMN_LABEL.get(key, {}).get(lang), f"{key}/{lang}"
                )

    def test_unknown_future_codes_are_not_dressed_up(self):
        self.assertEqual(copy_brief.check("some_future_check", "zh"), "some_future_check")
        self.assertEqual(copy_brief.reason("some_future_reason", None, "zh"), "some_future_reason")

    def test_negative_stock_check_state_and_reason_render_in_both_languages(self):
        for lang in _LANGS:
            self.assertTrue(copy_brief.check(tools_signoff.CHECK_NEGATIVE_STOCK, lang))
            self.assertTrue(copy_brief.state(tools_signoff.STATE_WARN, lang))
            text = copy_brief.reason("negative_stock", 3, lang)
            self.assertIn("3", text)
        # 「提醒」不是「没过」——不同状态不能渲染成同一句话(与 test_unknown_state_is_not_worded_as_failed 同一条口径)。
        self.assertNotEqual(
            copy_brief.state(tools_signoff.STATE_WARN, "zh"),
            copy_brief.state(tools_signoff.STATE_BLOCKED, "zh"),
        )


def _assert_table(case: unittest.TestCase, art: dict) -> None:
    """B2 的形状契约:columns=[{key,label}] + 行是 dict 且按 key 取得到值(标量)。"""
    case.assertEqual(art["kind"], "table")
    case.assertTrue(art["label"])
    case.assertTrue(art["columns"])
    for col in art["columns"]:
        case.assertEqual(set(col), {"key", "label"})
        case.assertTrue(col["label"])
    keys = {c["key"] for c in art["columns"]}
    for row in art["rows"]:
        case.assertIsInstance(row, dict)
        case.assertEqual(set(row), keys)
        for value in row.values():
            case.assertNotIsInstance(value, (dict, list))


if __name__ == "__main__":
    unittest.main()
