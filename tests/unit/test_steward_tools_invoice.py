# -*- coding: utf-8 -*-
"""管家单票体检 invoice_detail(services/steward/tools_invoice.py · B4)。

锁四条:①票的定位与写工具 erp_push 共用同一段(同一个 DAL、同一套保留期与可见性、同样的
查无/多义错误码);②推送历史来自 erp_push_logs 而非另起口径;③作用域外的票当查无,不泄露
"存在但你看不到";④套餐闸拒绝时诚实报错,不抛给对话层。零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.erp import push_log_queries
from services.ocr_history import queries as history_queries
from services.steward import tool_scope, tools_invoice
from services.steward.registry import ToolContext

_TODAY = date(2026, 7, 10)
_ROW = {
    "id": "h1",
    "filename": "7-11.pdf",
    "invoice_no": "RR581231-002",
    "seller_name": "7-11",
    "invoice_date": "2026-06-30",
    "total_amount": 401621.5,
    "workspace_client_id": 1,
}


def _ctx(allowed=None):
    return ToolContext(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        allowed_client_ids=allowed,
        today=_TODAY,
    )


def _search(items):
    """按写工具那条路的桩法接住定位段:套餐闸 + 可见性 + 同一个 list_ocr_history。"""
    return (
        mock.patch("core.route_helpers._check_history_access", return_value=90),
        mock.patch("core.db.get_visible_client_ids_for_user", return_value=[1]),
        mock.patch.object(
            history_queries, "list_ocr_history", return_value={"items": items, "total": len(items)}
        ),
    )


def _run(args, items, detail=None, push=None, ctx=None):
    gates = _search(items)
    with (
        gates[0],
        gates[1],
        gates[2],
        mock.patch.object(
            history_queries, "get_ocr_history_detail", return_value=detail
        ) as det_call,
        mock.patch.object(
            push_log_queries,
            "list_push_logs",
            return_value=push or {"items": [], "total": 0},
        ) as push_call,
    ):
        return tools_invoice.invoice_detail(ctx or _ctx(), args), det_call, push_call


class LocateTests(unittest.TestCase):
    def test_empty_keyword_never_picks_the_most_recent_one(self):
        res, _det, _push = _run({"keyword": "  "}, [_ROW])
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_INVOICE_NOT_FOUND)

    def test_no_hit_refuses_with_the_keyword(self):
        res, _det, _push = _run({"keyword": "7-11"}, [])
        self.assertEqual(res.error_code, tool_scope.ERR_INVOICE_NOT_FOUND)
        self.assertEqual(res.data["keyword"], "7-11")

    def test_ambiguous_keyword_returns_candidates_instead_of_guessing(self):
        res, _det, _push = _run({"keyword": "7-11"}, [_ROW, {**_ROW, "id": "h2"}])
        self.assertEqual(res.error_code, tool_scope.ERR_INVOICE_AMBIGUOUS)
        self.assertEqual(res.data["total"], 2)
        self.assertEqual(res.data["candidates"][0]["invoice_no"], "RR581231-002")

    def test_plan_gate_refusal_is_reported_not_raised(self):
        from fastapi import HTTPException

        with mock.patch(
            "core.route_helpers._check_history_access",
            side_effect=HTTPException(403, detail="history.upgrade_required"),
        ):
            res = tools_invoice.invoice_detail(_ctx(), {"keyword": "x"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_HISTORY_FORBIDDEN)

    def test_out_of_scope_invoice_reads_as_not_found(self):
        res, _det, _push = _run(
            {"keyword": "7-11"},
            [_ROW],
            detail={**_ROW, "workspace_client_id": 9},
            ctx=_ctx(allowed=frozenset({1})),
        )
        self.assertEqual(res.error_code, tool_scope.ERR_INVOICE_NOT_FOUND)


class DetailTests(unittest.TestCase):
    def test_shape_carries_face_fields_and_posting_kind(self):
        detail = {**_ROW, "posting_kind": "stock", "confidence": 0.97, "edited": True}
        res, det_call, push_call = _run({"keyword": "RR581231-002"}, [_ROW], detail=detail)
        self.assertTrue(res.ok)
        self.assertEqual(det_call.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(push_call.call_args.kwargs["history_id"], "h1")
        self.assertEqual(res.data["invoice_no"], "RR581231-002")
        self.assertEqual(res.data["total_amount"], "401621.50")  # 钱走 decimal,不过 float
        self.assertEqual(res.data["posting_kind"], "stock")
        self.assertTrue(res.data["edited"])

    def test_detail_row_missing_falls_back_to_the_search_hit(self):
        """详情读不回来(权限窄一层/刚被删)也不空手而归:列表那行的字段照样交出去。"""
        res, _det, _push = _run({"keyword": "7-11"}, [_ROW], detail=None)
        self.assertTrue(res.ok)
        self.assertEqual(res.data["seller_name"], "7-11")
        self.assertEqual(res.data["posting_kind"], "")

    def test_never_pushed_is_zero_not_missing(self):
        res, _det, _push = _run({"keyword": "7-11"}, [_ROW], detail=_ROW)
        self.assertEqual(res.data["push_count"], 0)
        self.assertEqual(res.data["push_status"], "")
        self.assertEqual(res.data["push_rows"], [])

    def test_push_failure_face_comes_from_the_push_log(self):
        push = {
            "items": [
                {
                    "status": "failed",
                    "error_code": "ERR_NO_ACC",
                    "category": "account_missing",
                    "created_at": datetime(2026, 7, 9, 3, 0, tzinfo=timezone.utc),
                },
                {"status": "failed", "error_code": "ERR_NO_ACC", "created_at": None},
            ],
            "total": 2,
        }
        res, _det, _push = _run({"keyword": "7-11"}, [_ROW], detail=_ROW, push=push)
        self.assertEqual(res.data["push_count"], 2)
        self.assertEqual(res.data["push_status"], "failed")
        self.assertEqual(res.data["push_error_code"], "ERR_NO_ACC")
        self.assertEqual(res.data["push_category"], "account_missing")
        self.assertEqual(res.data["push_at"], "2026-07-09T03:00:00+00:00")
        self.assertEqual(len(res.data["push_rows"]), 2)


if __name__ == "__main__":
    unittest.main()
