# -*- coding: utf-8 -*-
"""管家月结产线四问是既有服务层的薄封装(services/steward/tools_close.py · B4)。

薄封装不是口号,是断言:每个用例都 patch 掉被包的那个服务层函数,证明工具真的走了它
(而不是自己另抄一份 SQL/口径)。另外钉死四条容易在这几个工具上破的线:
  ① 账套作用域:被分派成员在对话里也只看得见分到的账套;
  ② 截止日必须经法定顺延现算(裸日期直接示人 = 让会计白加一天班),且逾期锚 e-Filing 日 ——
     与矩阵页/看板的 isOverdue 同一把尺,不然同一个格子两处结论相反;
  ③ 「还没算出来」不许渲染成 0(has_numbers / has_recon 分开报);
  ④ 枚举外的严重度不拿去查库。
零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.steward import tool_scope, tools_close
from services.steward.registry import ToolContext
from services.workorder import api as wo_api, matrix, review

_TODAY = date(2026, 7, 10)


def _ctx(allowed=None):
    return ToolContext(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        allowed_client_ids=allowed,
        today=_TODAY,
    )


def _ctx_on(today: date):
    ctx = _ctx()
    ctx.today = today
    return ctx


class _CurCM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _no_db():
    return mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM())


_CLIENTS = [
    {"id": 1, "name": "Sister Makeup", "tax_id": "0105500001234"},
    {"id": 2, "name": "62AHATAI", "tax_id": "0105500009999"},
]


def _matrix_row(**over):
    row = {
        "client_id": 1,
        "client_name": "Sister Makeup",
        "client_tax_id": None,
        "obligation_code": "pp30",
        "obligation_status": "due",
        "due_paper": date(2026, 7, 15),
        "due_efiling": date(2026, 7, 23),
        "work_order_id": "w1",
        "order_status": "collecting",
        "display_names": None,
    }
    row.update(over)
    return row


class DueSoonTests(unittest.TestCase):
    def _run(self, rows, ctx=None):
        with _no_db(), mock.patch.object(matrix, "fetch_rows", return_value=rows) as fetch:
            return tools_close.due_soon(ctx or _ctx(), {"period": "2569-07"}), fetch

    def test_wraps_matrix_service_and_counts_overdue(self):
        rows = [
            _matrix_row(due_efiling=date(2026, 7, 15)),  # 距 7-10 还有 5 天
            _matrix_row(client_id=2, client_name="62AHATAI", due_efiling=date(2026, 7, 7)),
        ]
        res, fetch = self._run(rows)
        self.assertEqual(fetch.call_args.kwargs["period"], "2569-07")
        self.assertEqual(fetch.call_args.kwargs["tenant_id"], "t-1")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["total"], 2)
        self.assertEqual(res.data["overdue"], 1)
        self.assertEqual(res.data["due_soon"], 1)
        self.assertEqual(
            [r["client_name"] for r in res.data["rows"]], ["62AHATAI", "Sister Makeup"]
        )
        self.assertEqual(res.data["rows"][0]["days_left"], -3)

    def test_overdue_anchors_the_efiling_date_like_the_matrix_page(self):
        """纸质 15 日已过、e-Filing 23 日还没到的那一周(ภ.พ.30 每月 16–23 号):矩阵页的
        isOverdue 读 due_efiling_deferred 说"还剩 5 天",这里必须给同一个结论。"""
        res, _ = self._run([_matrix_row()], ctx=_ctx_on(date(2026, 7, 18)))
        row = res.data["rows"][0]
        self.assertEqual(row["due"], "2026-07-23")
        self.assertEqual(row["days_left"], 5)
        self.assertEqual(res.data["overdue"], 0)
        # 纸质日与它的倒计时照样带出去,答复层据此说清"这是电子申报的日子"。
        self.assertEqual(row["due_paper"], "2026-07-15")
        self.assertEqual(row["days_left_paper"], -3)

    def test_due_date_is_deferred_over_weekend(self):
        """截止日落周六 → 顺延到下个工作日。裸日期直接示人会让人按 7-18 赶工。"""
        res, _ = self._run([_matrix_row(due_efiling=date(2026, 7, 18))])
        self.assertEqual(res.data["rows"][0]["due"], "2026-07-20")
        self.assertEqual(res.data["rows"][0]["days_left"], 10)

    def test_paper_only_obligation_falls_back_to_the_paper_date(self):
        """没有 e-Filing 日的义务(纸质申报)不能因此变成"没有截止日"。"""
        res, _ = self._run([_matrix_row(due_efiling=None)])
        self.assertEqual(res.data["rows"][0]["due"], "2026-07-15")
        self.assertEqual(res.data["rows"][0]["days_left"], 5)

    def test_nil_and_unmaterialised_and_frozen_are_not_owed(self):
        rows = [
            _matrix_row(obligation_status="nil"),
            _matrix_row(client_id=2, obligation_status=None, work_order_id=None),
            _matrix_row(client_id=2, order_status="archive"),
        ]
        res, _ = self._run(rows)
        self.assertEqual(res.data["total"], 0)
        self.assertEqual(res.data["rows"], [])

    def test_scope_filter_drops_unassigned_clients(self):
        rows = [_matrix_row(), _matrix_row(client_id=2, client_name="62AHATAI")]
        res, _ = self._run(rows, ctx=_ctx(allowed=frozenset({1})))
        self.assertEqual(res.data["total"], 1)
        self.assertEqual(res.data["rows"][0]["client_name"], "Sister Makeup")

    def test_missing_due_date_is_counted_honestly_not_as_due_soon(self):
        res, _ = self._run([_matrix_row(due_paper=None, due_efiling=None)])
        self.assertEqual(res.data["no_due_date"], 1)
        self.assertEqual(res.data["due_soon"], 0)
        self.assertIsNone(res.data["rows"][0]["days_left"])


def _queue(orders):
    clients = {}
    for o in orders:
        clients.setdefault(o["workspace_client_id"], {**o, "orders": []})["orders"].append(o)
    return {"clients": list(clients.values()), "flagged_items": [], "counts": {}}


def _order(**over):
    order = {
        "work_order_id": "w1",
        "workspace_client_id": 1,
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "status": "review",
        "flagged_total": 3,
        "top_severity": "crit",
        "next_due_efiling": "2026-07-23",
        "next_due_paper": "2026-07-15",
    }
    order.update(over)
    return order


class ReviewQueueTests(unittest.TestCase):
    def _run(self, args, orders, ctx=None):
        with (
            _no_db(),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(review, "review_queue", return_value=_queue(orders)) as q,
            mock.patch("core.feature_flags.pearnly_ai_sod_enabled_for", return_value=False),
        ):
            return tools_close.review_queue(ctx or _ctx(), args), q

    def test_wraps_review_read_model_with_actor_identity(self):
        res, q = self._run({}, [_order(), _order(work_order_id="w2", flagged_total=1)])
        self.assertEqual(q.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(q.call_args.kwargs["actor"], "user:u1")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["order_count"], 2)
        self.assertEqual(res.data["client_count"], 1)
        self.assertEqual(res.data["flagged_count"], 4)
        self.assertEqual(res.data["rows"][0]["severity"], "crit")

    def test_empty_queue_is_reported_not_faked(self):
        res, _ = self._run({}, [])
        self.assertTrue(res.ok)
        self.assertEqual(res.data["order_count"], 0)
        self.assertEqual(res.data["rows"], [])

    def test_bogus_severity_is_not_taken_to_the_database(self):
        _res, q = self._run({"severity": "catastrophic"}, [])
        self.assertIsNone(q.call_args.kwargs["severity"])

    def test_client_filter_grounds_on_the_real_roster(self):
        _res, q = self._run({"client_name": "makeup"}, [])
        self.assertEqual(q.call_args.kwargs["client_id"], 1)

    def test_unknown_client_refuses_instead_of_querying_everything(self):
        res, q = self._run({"client_name": "nobody"}, [])
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)
        q.assert_not_called()

    def test_scope_filter_drops_unassigned_clients(self):
        res, _ = self._run(
            {},
            [_order(), _order(work_order_id="w2", workspace_client_id=9, client_name="X")],
            ctx=_ctx(allowed=frozenset({1})),
        )
        self.assertEqual(res.data["order_count"], 1)


class _OrderDetailCase(unittest.TestCase):
    def _run(self, fn, detail, args=None, orders=(("w1",),)):
        listing = {"orders": [{"id": o[0]} for o in orders], "count": len(orders)}
        with (
            _no_db(),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(wo_api, "list_orders", return_value=listing) as lst,
            mock.patch.object(wo_api, "order_detail", return_value=detail) as det,
        ):
            res = fn(_ctx(), {"client_name": "makeup", "period": "2569-07", **(args or {})})
        return res, lst, det


class TaxNumbersTests(_OrderDetailCase):
    def test_wraps_order_detail_numbers_as_decimal_strings(self):
        detail = {
            "status": "review",
            "current_step": "compute",
            "numbers": {
                "sales_amount": 1000000,
                "output_vat": "70000.005",
                "purchase_amount": 400000,
                "input_vat": 28000,
                "tax_due": 42000,
            },
        }
        res, lst, det = self._run(tools_close.tax_numbers, detail)
        self.assertEqual(lst.call_args.kwargs["workspace_client_id"], 1)
        det.assert_called_once()
        self.assertTrue(res.data["has_numbers"])
        self.assertEqual(res.data["sales_amount"], "1000000.00")
        self.assertEqual(res.data["output_vat"], "70000.00")  # 钱走 decimal,不过 float
        self.assertEqual(res.data["tax_due"], "42000.00")

    def test_engine_has_not_computed_yet_is_not_dressed_up_as_zero(self):
        res, _lst, _det = self._run(
            tools_close.tax_numbers,
            {"status": "running", "current_step": "classify", "numbers": {}},
        )
        self.assertTrue(res.ok)
        self.assertTrue(res.data["has_order"])
        self.assertFalse(res.data["has_numbers"])
        self.assertNotIn("tax_due", res.data)

    def test_no_order_reported_honestly(self):
        res, _lst, det = self._run(tools_close.tax_numbers, None, orders=())
        self.assertTrue(res.ok)
        self.assertFalse(res.data["has_order"])
        det.assert_not_called()

    def test_unknown_client_refuses_instead_of_guessing(self):
        with _no_db(), mock.patch.object(tool_scope, "clients", return_value=_CLIENTS):
            res = tools_close.tax_numbers(_ctx(), {"client_name": "nobody"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)


class BankReconStatusTests(_OrderDetailCase):
    _RECON = {
        "auto_matched_count": 12,
        "review_count": 2,
        "missing_invoice": [
            {"amount": "4500.00", "tx_date": "2026-06-11", "description": "PAYMENT 7-11"}
        ],
        "unmatched_invoice": [{"candidate_id": "c1"}],
        "diff": {
            "missing_invoice_total": "4500",
            "unmatched_invoice_total": "1200",
            "net": "3300",
        },
    }

    def test_wraps_order_detail_bank_recon(self):
        res, _lst, _det = self._run(
            tools_close.bank_recon_status, {"status": "review", "bank_recon": self._RECON}
        )
        self.assertTrue(res.data["has_recon"])
        self.assertEqual(res.data["auto_matched"], 12)  # 落库时算好的 *_count 优先
        self.assertEqual(res.data["missing_invoice"], 1)  # 没有 *_count 就数清单
        self.assertEqual(res.data["net"], "3300.00")
        self.assertEqual(res.data["rows"][0]["description"], "PAYMENT 7-11")

    def test_no_recon_is_not_dressed_up_as_balanced(self):
        res, _lst, _det = self._run(
            tools_close.bank_recon_status, {"status": "collecting", "bank_recon": None}
        )
        self.assertTrue(res.ok)
        self.assertFalse(res.data["has_recon"])
        self.assertNotIn("net", res.data)

    def test_no_order_reported_honestly(self):
        res, _lst, _det = self._run(tools_close.bank_recon_status, None, orders=())
        self.assertFalse(res.data["has_order"])
        self.assertFalse(res.data["has_recon"])

    def test_unknown_client_refuses_instead_of_guessing(self):
        with _no_db(), mock.patch.object(tool_scope, "clients", return_value=_CLIENTS):
            res = tools_close.bank_recon_status(_ctx(), {"client_name": "nobody"})
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
