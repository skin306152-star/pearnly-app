# -*- coding: utf-8 -*-
"""管家六工具是既有服务层的薄封装(services/steward/tools.py · B2-M1)。

薄封装不是口号,是断言:每个用例都 patch 掉被包的那个服务层函数,证明工具真的走了它
(而不是自己另抄一份 SQL/口径)。顺带锁:账套作用域过滤、枚举外状态不进查询、时间窗过滤、
套餐闸拒绝时诚实报错。零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.erp import push_log_queries
from services.ocr_history import queries as history_queries
from services.steward import registry, tool_scope, tools
from services.steward.registry import ToolContext
from services.workorder import api as wo_api, matrix, obligation_engine
from services.workspace import store as ws_store

_TODAY = date(2026, 7, 26)


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


_CLIENTS = [
    {"id": 1, "name": "Sister Makeup", "tax_id": "0105500001234"},
    {"id": 2, "name": "62AHATAI", "tax_id": "0105500009999"},
]


class MatchClientsTests(unittest.TestCase):
    def test_exact_name_wins_over_substring(self):
        rows = [
            {"id": 1, "name": "Sister", "tax_id": None},
            {"id": 2, "name": "Sister Makeup", "tax_id": None},
        ]
        self.assertEqual([c["id"] for c in tool_scope.match_clients(rows, "sister")], [1])

    def test_substring_and_tax_id(self):
        self.assertEqual([c["id"] for c in tool_scope.match_clients(_CLIENTS, "makeup")], [1])
        self.assertEqual([c["id"] for c in tool_scope.match_clients(_CLIENTS, "9999")], [2])

    def test_empty_keyword_matches_nothing(self):
        self.assertEqual(tool_scope.match_clients(_CLIENTS, "  "), [])


class MatrixOverviewTests(unittest.TestCase):
    def _rows(self):
        return [
            {
                "client_id": 1,
                "client_name": "A",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": "w1",
                "order_status": "collecting",
                "display_names": None,
                "client_tax_id": None,
            },
            {
                "client_id": 2,
                "client_name": "B",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": None,
                "due_efiling": None,
                "work_order_id": "w2",
                "order_status": "review",
                "display_names": None,
                "client_tax_id": None,
            },
        ]

    def test_wraps_matrix_service_and_counts_badges(self):
        with _no_db(), mock.patch.object(matrix, "fetch_rows", return_value=self._rows()) as fetch:
            res = tools.matrix_overview(_ctx(), {"period": "2569-06"})
        fetch.assert_called_once()
        self.assertEqual(fetch.call_args.kwargs["period"], "2569-06")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["client_count"], 2)
        self.assertEqual(res.data["badges"]["missing_materials"], 1)
        self.assertEqual(res.data["badges"]["pending_review"], 1)
        self.assertEqual({a["name"] for a in res.data["attention"]}, {"A", "B"})

    def test_scope_filter_drops_unassigned_clients(self):
        with _no_db(), mock.patch.object(matrix, "fetch_rows", return_value=self._rows()):
            res = tools.matrix_overview(_ctx(allowed=frozenset({1})), {})
        self.assertEqual(res.data["client_count"], 1)

    def test_period_defaults_to_current_be_period(self):
        with _no_db(), mock.patch.object(matrix, "fetch_rows", return_value=[]) as fetch:
            tools.matrix_overview(_ctx(), {})
        self.assertEqual(fetch.call_args.kwargs["period"], obligation_engine.current_be_period())


class ClientStatusTests(unittest.TestCase):
    def test_wraps_workorder_api(self):
        detail = {
            "id": "w1",
            "status": "collecting",
            "current_step": "intake",
            "material_count": 4,
            "needs": [{"kind": "purchase_invoices"}],
            "blocked_reasons": [],
            "flagged": [],
        }
        with (
            _no_db(),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(
                wo_api, "list_orders", return_value={"orders": [{"id": "w1"}], "count": 1}
            ) as lst,
            mock.patch.object(wo_api, "order_detail", return_value=detail) as det,
        ):
            res = tools.client_status(_ctx(), {"client_name": "makeup", "period": "2569-06"})
        self.assertEqual(lst.call_args.kwargs["workspace_client_id"], 1)
        det.assert_called_once()
        self.assertTrue(res.ok)
        self.assertEqual(res.data["client_name"], "Sister Makeup")
        self.assertEqual(res.data["status"], "collecting")
        self.assertEqual(len(res.data["needs"]), 1)

    def test_unknown_client_refuses_instead_of_guessing(self):
        with _no_db(), mock.patch.object(tool_scope, "clients", return_value=_CLIENTS):
            res = tools.client_status(_ctx(), {"client_name": "nobody"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools.ERR_CLIENT_NOT_FOUND)

    def test_ambiguous_client_refuses_with_candidates(self):
        rows = [
            {"id": 1, "name": "Siam A", "tax_id": None},
            {"id": 2, "name": "Siam B", "tax_id": None},
        ]
        with _no_db(), mock.patch.object(tool_scope, "clients", return_value=rows):
            res = tools.client_status(_ctx(), {"client_name": "siam"})
        self.assertEqual(res.error_code, tools.ERR_CLIENT_AMBIGUOUS)
        self.assertEqual(len(res.data["candidates"]), 2)

    def test_no_order_is_reported_honestly(self):
        with (
            _no_db(),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch(
                "services.workorder.api.list_orders", return_value={"orders": [], "count": 0}
            ),
        ):
            res = tools.client_status(_ctx(), {"client_name": "62AHATAI"})
        self.assertTrue(res.ok)
        self.assertFalse(res.data["has_order"])


class WorkorderListTests(unittest.TestCase):
    _ORDERS = [
        {"id": "w1", "workspace_client_id": 1, "status": "running", "current_step": "classify"}
    ]

    def _run(self, args):
        with (
            _no_db(),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(
                wo_api, "list_orders", return_value={"orders": self._ORDERS, "count": 1}
            ) as lst,
        ):
            return tools.workorder_list(_ctx(), args), lst

    def test_wraps_list_orders_and_drops_bogus_status(self):
        res, lst = self._run({"status": "almost_done", "period": "2569-06"})
        self.assertIsNone(lst.call_args.kwargs["statuses"])  # 枚举外不拿去查库
        self.assertIsNone(res.data["status_filter"])
        self.assertEqual(res.data["counts"], {"running": 1})
        self.assertEqual(res.data["orders"][0]["client_name"], "Sister Makeup")

    def test_pending_review_matches_matrix_badge_scope(self):
        """「还没审完」= 矩阵的「待审」= stuck + review。少查一态就会与同屏矩阵打架。"""
        res, lst = self._run({"status": "pending_review", "period": "2569-07"})
        self.assertEqual(sorted(lst.call_args.kwargs["statuses"]), ["review", "stuck"])
        self.assertEqual(res.data["status_filter"], "pending_review")

    def test_raw_engine_status_is_widened_to_its_group(self):
        """大脑照旧吐 'review' 也不再漏掉 stuck —— 口径只有一份,入口用哪个词都归它。"""
        _res, lst = self._run({"status": "review"})
        self.assertEqual(sorted(lst.call_args.kwargs["statuses"]), ["review", "stuck"])


class PushLogQueryTests(unittest.TestCase):
    def _items(self):
        now = datetime.now(timezone.utc)
        return [
            {
                "status": "success",
                "created_at": now,
                "invoice_no": "A1",
                "workspace_name": "Sister Makeup",
            },
            {
                "status": "failed",
                "created_at": now,
                "invoice_no": "A2",
                "workspace_name": "62AHATAI",
                "category": "account_missing",
                "error_code": "ERR_NO_ACC",
            },
            {
                "status": "failed",
                "created_at": now - timedelta(days=40),
                "invoice_no": "OLD",
                "workspace_name": "Sister Makeup",
                "category": "account_missing",
            },
        ]

    def test_wraps_push_log_queries_and_filters_window(self):
        with mock.patch.object(
            push_log_queries, "list_push_logs", return_value={"items": self._items(), "total": 3}
        ) as query:
            res = tools.push_log_query(_ctx(), {"days": "7"})
        self.assertEqual(query.call_args.kwargs["user_id"], "u1")
        self.assertEqual(query.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(res.data["total"], 2)  # 40 天前那条被时间窗滤掉
        self.assertEqual(res.data["success"], 1)
        self.assertEqual(res.data["failed"], 1)
        self.assertEqual(res.data["reasons"], {"account_missing": 1})

    def test_client_filter_matches_subject(self):
        with mock.patch.object(
            push_log_queries, "list_push_logs", return_value={"items": self._items(), "total": 3}
        ):
            res = tools.push_log_query(_ctx(), {"client_name": "62AHATAI"})
        self.assertEqual(res.data["total"], 1)

    def test_days_clamped(self):
        with mock.patch.object(
            push_log_queries, "list_push_logs", return_value={"items": [], "total": 0}
        ):
            self.assertEqual(tools.push_log_query(_ctx(), {"days": "9999"}).data["days"], 90)
            self.assertEqual(tools.push_log_query(_ctx(), {"days": "ครับ"}).data["days"], 7)


class HistoryQueryTests(unittest.TestCase):
    def test_wraps_history_dal_with_plan_retention_and_visibility(self):
        items = [
            {
                "id": "h1",
                "filename": "a.pdf",
                "invoice_no": "INV1",
                "seller_name": "7-11",
                "invoice_date": "2026-06-01",
                "status": "confirmed",
            }
        ]
        with (
            mock.patch("core.route_helpers._check_history_access", return_value=90),
            mock.patch("core.db.get_visible_client_ids_for_user", return_value=[5]),
            mock.patch.object(
                history_queries, "list_ocr_history", return_value={"items": items, "total": 1}
            ) as dal,
        ):
            res = tools.history_query(_ctx(), {"keyword": "7-11"})
        self.assertEqual(dal.call_args.kwargs["retention_days"], 90)
        self.assertEqual(dal.call_args.kwargs["restrict_client_ids"], [5])
        self.assertEqual(res.data["rows"][0]["invoice_no"], "INV1")

    def test_plan_gate_refusal_is_reported_not_raised(self):
        from fastapi import HTTPException

        with mock.patch(
            "core.route_helpers._check_history_access",
            side_effect=HTTPException(403, detail="history.upgrade_required"),
        ):
            res = tools.history_query(_ctx(), {"keyword": "x"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools.ERR_HISTORY_FORBIDDEN)


class ClientLookupTests(unittest.TestCase):
    def test_wraps_workspace_store(self):
        rows = [{"id": 1, "name": "Sister Makeup", "tax_id": "0105500001234"}]
        with mock.patch.object(ws_store, "list_workspace_clients", return_value=rows) as dal:
            res = tools.run(registry.CLIENT_LOOKUP, _ctx(), {"keyword": "sister"})
        self.assertEqual(dal.call_args.args[1], "t-1")
        self.assertEqual(res.data["total"], 1)
        self.assertEqual(res.data["clients"][0]["id"], 1)

    def test_scope_ids_passed_to_dal(self):
        with mock.patch.object(ws_store, "list_workspace_clients", return_value=[]) as dal:
            tools.client_lookup(_ctx(allowed=frozenset({3, 4})), {"keyword": "x"})
        self.assertEqual(sorted(dal.call_args.kwargs["restrict_ids"]), [3, 4])


if __name__ == "__main__":
    unittest.main()
