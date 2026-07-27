# -*- coding: utf-8 -*-
"""管家本期盘点两问(services/steward/tools_period.py)。

薄封装不是口号,是断言:每个用例都 patch 掉被包的服务层函数,证明工具真的走了它。另外钉死
这两个工具最容易破的六条:
  ① 批量读:30 家客户只准打两条 SQL(矩阵一条 + 交付物一条),逐单查就是 N+1;
  ② 数字全由代码从库里取并用 Decimal 相加(负数留抵、零、超大值、分位都有边界用例);
  ③ 没算出税额的行不许填 0(假零比说不知道危险得多);
  ④ 账套作用域:被分派成员在对话里也只看得见分到的账套;
  ⑤ 六态互斥且穷尽 —— counts 之和 = total,「已推 X 张、还差 Y 张」才立得住;
  ⑥ 枚举外的 filter 不拿去筛(当没筛,不猜)。
零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.erp import push_log_queries
from services.steward import tool_scope, tools_period
from services.steward.registry import ToolContext
from services.workorder import api as wo_api, matrix, store as wo_store

_TODAY = date(2026, 7, 10)
_PERIOD = "2569-07"

_CLIENTS = [
    {"id": 1, "name": "Sister Makeup", "tax_id": "0105500001234"},
    {"id": 2, "name": "62AHATAI", "tax_id": "0105500009999"},
]


def _ctx(allowed=None):
    return ToolContext(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        allowed_client_ids=allowed,
        today=_TODAY,
    )


class _CurCM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _no_db():
    return mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM())


def _matrix_row(client_id=1, name="Sister Makeup", work_order_id="w1"):
    return {
        "client_id": client_id,
        "client_name": name,
        "obligation_code": "pp30",
        "obligation_status": "due",
        "work_order_id": work_order_id,
        "order_status": "review",
    }


def _numbers(**over):
    base = {
        "sales_amount": "1000000.00",
        "output_vat": "70000.00",
        "purchase_amount": "500000.00",
        "input_vat": "35000.00",
        "tax_due": "35000.00",
    }
    base.update(over)
    return base


class TaxMatrixTests(unittest.TestCase):
    def _run(self, rows, numbers_by_order, ctx=None, args=None):
        with (
            _no_db(),
            mock.patch.object(matrix, "fetch_rows", return_value=rows) as fetch,
            mock.patch.object(
                matrix, "fetch_deliverable_numbers", return_value=numbers_by_order
            ) as fetch_numbers,
        ):
            res = tools_period.tax_matrix(
                ctx or _ctx(), {"period": _PERIOD} if args is None else args
            )
        return res, fetch, fetch_numbers

    def test_wraps_matrix_service_and_reads_deliverables_in_one_batch(self):
        rows = [_matrix_row(), _matrix_row(2, "62AHATAI", "w2")]
        res, fetch, fetch_numbers = self._run(
            rows, {"w1": _numbers(), "w2": _numbers(tax_due="12000.00")}
        )
        self.assertTrue(res.ok)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(fetch_numbers.call_count, 1)  # 逐家查 = N+1,这里钉死只查一次
        kwargs = fetch_numbers.call_args.kwargs
        self.assertEqual(sorted(kwargs["work_order_ids"]), ["w1", "w2"])
        self.assertEqual(kwargs["kind"], "pp30_draft")
        self.assertEqual(kwargs["tenant_id"], "t-1")
        self.assertEqual(res.data["client_count"], 2)
        self.assertEqual(res.data["ready"], 2)

    def test_totals_are_summed_with_decimal(self):
        rows = [_matrix_row(), _matrix_row(2, "62AHATAI", "w2")]
        numbers = {
            "w1": _numbers(tax_due="0.10", output_vat="0.10"),
            "w2": _numbers(tax_due="0.20", output_vat="0.20"),
        }
        res, _f, _n = self._run(rows, numbers)
        # float 相加这里会给 0.30000000000000004;Decimal 给 0.30。
        self.assertEqual(res.data["totals"]["tax_due"], "0.30")
        self.assertEqual(res.data["totals"]["output_vat"], "0.30")

    def test_credit_rows_are_counted_and_netted(self):
        """留抵(应交为负)在合计里冲抵别家,不单独点出来会被当成"少交了"。"""
        rows = [_matrix_row(), _matrix_row(2, "62AHATAI", "w2")]
        numbers = {"w1": _numbers(tax_due="35000.00"), "w2": _numbers(tax_due="-5000.00")}
        res, _f, _n = self._run(rows, numbers)
        self.assertEqual(res.data["credit"], 1)
        self.assertEqual(res.data["totals"]["tax_due"], "30000.00")

    def test_zero_tax_due_is_not_a_credit(self):
        res, _f, _n = self._run([_matrix_row()], {"w1": _numbers(tax_due="0")})
        self.assertEqual(res.data["credit"], 0)
        self.assertEqual(res.data["rows"][0]["tax_due"], "0.00")

    def test_huge_amount_is_not_silently_zeroed(self):
        """默认 Decimal 上下文只有 28 位精度,量化会抛 —— 被吞成 0.00 等于把大数印成零。"""
        huge = "123456789012345678901234567890.55"
        res, _f, _n = self._run([_matrix_row()], {"w1": _numbers(tax_due=huge)})
        self.assertEqual(res.data["rows"][0]["tax_due"], huge)
        self.assertEqual(res.data["totals"]["tax_due"], huge)

    def test_sub_cent_amounts_are_rounded_not_dropped(self):
        res, _f, _n = self._run([_matrix_row()], {"w1": _numbers(tax_due="0.005")})
        self.assertEqual(Decimal(res.data["rows"][0]["tax_due"]), Decimal("0.00"))

    def test_row_without_numbers_is_blank_not_zero(self):
        """还没算到税额的行填 0 会被当成"这家不用交",红线。"""
        res, _f, _n = self._run([_matrix_row()], {})
        row = res.data["rows"][0]
        self.assertEqual(row["state"], tools_period.TAX_NO_NUMBERS)
        for key in tool_scope.TAX_MONEY_KEYS:
            self.assertEqual(row[key], "", key)
        self.assertEqual(res.data["ready"], 0)
        self.assertEqual(res.data["totals"]["tax_due"], "0.00")

    def test_client_without_work_order_is_no_order(self):
        res, _f, _n = self._run([_matrix_row(work_order_id=None)], {})
        self.assertEqual(res.data["rows"][0]["state"], tools_period.TAX_NO_ORDER)
        self.assertEqual(res.data["no_order"], 1)

    def test_client_rows_are_merged_across_obligations(self):
        """一家这期可能好几张工单(ภ.พ.30 之外还有 ภ.ง.ด.),表里仍然只占一行。"""
        rows = [_matrix_row(work_order_id="w-pnd"), _matrix_row(work_order_id="w1")]
        res, _f, _n = self._run(rows, {"w1": _numbers()})
        self.assertEqual(len(res.data["rows"]), 1)
        self.assertEqual(res.data["rows"][0]["state"], tools_period.TAX_READY)

    def test_ready_rows_sort_by_tax_due_desc_then_pending_by_name(self):
        rows = [
            _matrix_row(1, "Small", "w1"),
            _matrix_row(2, "Big", "w2"),
            _matrix_row(3, "Zeta", "w3"),
        ]
        numbers = {"w1": _numbers(tax_due="10.00"), "w2": _numbers(tax_due="900000.00")}
        res, _f, _n = self._run(rows, numbers)
        self.assertEqual([r["client_name"] for r in res.data["rows"]], ["Big", "Small", "Zeta"])

    def test_scope_hides_other_clients(self):
        rows = [_matrix_row(), _matrix_row(2, "62AHATAI", "w2")]
        res, _f, fetch_numbers = self._run(
            rows, {"w1": _numbers()}, ctx=_ctx(allowed=frozenset({1}))
        )
        self.assertEqual([r["client_id"] for r in res.data["rows"]], [1])
        # 越界那家的工单号连查都不该查(作用域是读闸,不是显示闸)。
        self.assertEqual(fetch_numbers.call_args.kwargs["work_order_ids"], ["w1"])

    def test_empty_scope_returns_empty_table_not_error(self):
        res, _f, _n = self._run([], {})
        self.assertTrue(res.ok)
        self.assertEqual(res.data["client_count"], 0)
        self.assertEqual(res.data["rows"], [])
        self.assertEqual(res.data["totals"]["tax_due"], "0.00")

    def test_period_defaults_to_current_when_missing(self):
        with mock.patch.object(tool_scope, "period_or_current", return_value="2569-06") as p:
            res, _f, _n = self._run([], {}, args={})
        p.assert_called_once_with(None)
        self.assertEqual(res.data["period"], "2569-06")

    def test_rows_are_truncated_but_totals_are_not(self):
        rows = [
            _matrix_row(i, f"C{i:03d}", f"w{i}")
            for i in range(1, tools_period.MATRIX_ROW_LIMIT + 6)
        ]
        numbers = {f"w{i}": _numbers(tax_due="1.00") for i in range(1, len(rows) + 1)}
        res, _f, _n = self._run(rows, numbers)
        self.assertEqual(len(res.data["rows"]), tools_period.MATRIX_ROW_LIMIT)
        self.assertTrue(res.data["truncated"])
        self.assertEqual(res.data["totals"]["tax_due"], f"{len(rows)}.00")


class PeriodInvoiceTests(unittest.TestCase):
    def _run(self, invoices, push_rows, args=None, orders=None):
        listing = {"orders": [{"id": "w1"}] if orders is None else orders, "count": 1}
        with (
            _no_db(),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(wo_api, "list_orders", return_value=listing),
            mock.patch.object(wo_store, "list_items", return_value=[{"id": "i1"}]),
            mock.patch.object(wo_store, "list_events", return_value=[]),
            mock.patch(
                "services.workorder.push_coverage.counted_purchase_invoices",
                return_value=invoices,
            ),
            mock.patch.object(
                push_log_queries, "list_push_logs_by_invoice_nos", return_value=push_rows
            ) as dal,
        ):
            res = tools_period.period_invoices(
                _ctx(), args or {"client_name": "Sister Makeup", "period": _PERIOD}
            )
        return res, dal

    @staticmethod
    def _invoice(no, **over):
        row = {
            "item_id": f"i-{no}",
            "invoice_no": no,
            "invoice_date": "2026-06-30",
            "vendor": "7-11",
            "total_amount": "107.00",
            "file_ref": "a.pdf",
            "item_status": "ok",
            "awaiting_decision": False,
        }
        row.update(over)
        return row

    def test_pushed_and_never_are_told_apart(self):
        res, dal = self._run(
            [self._invoice("IV-1"), self._invoice("IV-2")],
            [{"invoice_no": "IV-1", "status": "success"}],
        )
        self.assertTrue(res.ok)
        states = {r["invoice_no"]: r["state"] for r in res.data["rows"]}
        self.assertEqual(states, {"IV-1": "pushed", "IV-2": "never"})
        self.assertEqual(res.data["not_pushed"], 1)
        # 票号集一次查完(逐张查 = 每张一次往返)。
        self.assertEqual(dal.call_count, 1)
        self.assertEqual(dal.call_args.kwargs["invoice_nos"], ["IV-1", "IV-2"])
        self.assertEqual(dal.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(dal.call_args.kwargs["work_order_id"], "w1")

    def test_counts_are_exclusive_and_exhaustive(self):
        invoices = [
            self._invoice("IV-1"),
            self._invoice("IV-2"),
            self._invoice("IV-3"),
            self._invoice("IV-4", awaiting_decision=True, item_status="flagged"),
            self._invoice("", file_ref="scan-9.jpg"),
        ]
        push_rows = [
            {"invoice_no": "IV-1", "status": "success"},
            {"invoice_no": "IV-2", "status": "failed"},
            {"invoice_no": "IV-3", "status": "pending"},
        ]
        res, _dal = self._run(invoices, push_rows)
        counts = res.data["counts"]
        self.assertEqual(set(counts), set(tools_period.INVOICE_STATES))
        self.assertEqual(sum(counts.values()), res.data["total"])
        self.assertEqual(counts["pushed"], 1)
        self.assertEqual(counts["failed"], 1)
        self.assertEqual(counts["in_flight"], 1)
        self.assertEqual(counts[tools_period.INVOICE_PENDING_REVIEW], 1)
        self.assertEqual(counts[tools_period.INVOICE_NO_NUMBER], 1)
        self.assertEqual(res.data["not_pushed"], 4)

    def test_awaiting_decision_wins_over_push_state(self):
        """还没判完的票谈"推没推"没有意义 —— 先说待判,别让人去推一张要改的票。"""
        res, _dal = self._run(
            [self._invoice("IV-1", awaiting_decision=True)],
            [{"invoice_no": "IV-1", "status": "success"}],
        )
        self.assertEqual(res.data["rows"][0]["state"], tools_period.INVOICE_PENDING_REVIEW)

    def test_unreadable_invoice_no_falls_back_to_file_name(self):
        res, dal = self._run([self._invoice("", file_ref="scan-9.jpg")], [])
        row = res.data["rows"][0]
        self.assertEqual(row["invoice_no"], "scan-9.jpg")
        self.assertEqual(row["state"], tools_period.INVOICE_NO_NUMBER)
        dal.assert_not_called()  # 没有一个能查的票号 → 不打空查询

    def test_missing_amount_is_blank_not_zero(self):
        res, _dal = self._run([self._invoice("IV-1", total_amount=None)], [])
        self.assertEqual(res.data["rows"][0]["amount"], "")

    def test_not_pushed_filter_keeps_everything_but_pushed(self):
        invoices = [self._invoice("IV-1"), self._invoice("IV-2", awaiting_decision=True)]
        res, _dal = self._run(
            invoices,
            [{"invoice_no": "IV-1", "status": "success"}],
            args={"client_name": "Sister Makeup", "filter": "not_pushed"},
        )
        self.assertEqual([r["invoice_no"] for r in res.data["rows"]], ["IV-2"])
        self.assertEqual(res.data["total"], 2)  # 统计仍是全景,筛的只是清单

    def test_pending_review_filter(self):
        invoices = [self._invoice("IV-1"), self._invoice("IV-2", awaiting_decision=True)]
        res, _dal = self._run(
            invoices, [], args={"client_name": "Sister Makeup", "filter": "pending_review"}
        )
        self.assertEqual([r["invoice_no"] for r in res.data["rows"]], ["IV-2"])

    def test_unknown_filter_is_treated_as_no_filter(self):
        res, _dal = self._run(
            [self._invoice("IV-1")], [], args={"client_name": "Sister Makeup", "filter": "หายไป"}
        )
        self.assertEqual(res.data["filter"], tools_period.FILTER_ALL)
        self.assertEqual(len(res.data["rows"]), 1)

    def test_no_work_order_is_honest_not_empty_list(self):
        res, dal = self._run([], [], orders=[])
        self.assertTrue(res.ok)
        self.assertFalse(res.data["has_order"])
        self.assertEqual(res.data["total"], 0)
        dal.assert_not_called()

    def test_unknown_client_asks_back_instead_of_guessing(self):
        with _no_db(), mock.patch.object(tool_scope, "clients", return_value=_CLIENTS):
            res = tools_period.period_invoices(_ctx(), {"client_name": "หจก. ไม่มีจริง"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)

    def test_ambiguous_client_asks_back(self):
        rows = [{"id": 3, "name": "Sister A"}, {"id": 4, "name": "Sister B"}]
        with _no_db(), mock.patch.object(tool_scope, "clients", return_value=rows):
            res = tools_period.period_invoices(_ctx(), {"client_name": "Sister"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_AMBIGUOUS)

    def test_out_of_scope_client_is_invisible(self):
        """作用域外的账套连名录都不该出现 —— 报"查无此客户"而不是拒绝。"""
        with (
            _no_db(),
            mock.patch(
                "services.workspace.store.list_workspace_clients", return_value=[]
            ) as ws_list,
        ):
            res = tools_period.period_invoices(
                _ctx(allowed=frozenset({9})), {"client_name": "Sister Makeup"}
            )
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)
        self.assertEqual(ws_list.call_args.kwargs["restrict_ids"], [9])


if __name__ == "__main__":
    unittest.main()
